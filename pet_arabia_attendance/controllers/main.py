import pytz
from random import randint
from math import cos, asin, sqrt, pi
from odoo import http
from odoo import api
from odoo.http import request

from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class AttendanceController(http.Controller):

	@api.model
	def set_time_to_users_timezone(self, time, tz: str):
		local_timezone = pytz.timezone(tz)
		return time.astimezone(local_timezone).strftime('%-d-%b-%Y %-I:%M:%S %p')
	
	@api.model
	def Response(self, message, *, success=True, **kwargs):
		kwargs['message'] = message
		kwargs['success'] = success
		return kwargs

	@api.model
	def Error(*args, **kwargs):
		kwargs['success'] = False
		return args[0].Response(*args, **kwargs)

	@api.model
	def is_valid(self, obj, correct_cls):
		if obj == None:
			raise Exception("'None' value(s) found in your request i.e. There are missing values in your request")
		if not isinstance(obj, correct_cls):
			raise Exception(f"The field types are incorrect. Please check the data you have posted.")
		return obj

	@api.model
	def generate_passcode(self) -> str:
		"""Generate 6 digit random passcode"""
		num = randint(0, 999999)
		return str(num).rjust(6, '0')
	
	@api.model
	def coordinates_within_radius(self, lat1, lon1, lat2, lon2, radius) -> bool:
		p = pi/180
		a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p) * cos(lat2*p) * (1-cos((lon2-lon1)*p))/2
		distance = 12742 * asin(sqrt(a)) 
		return distance <= radius

	def is_employee_in_permitted_location(self, request, attendance_type, emp_id, curren_lat, current_lng):
		employee = request.env['hr.employee'].sudo().browse([emp_id])[0]
		if attendance_type == 'check_in' and employee.can_checkin_anywhere:
			return True
		if attendance_type == 'check_out' and employee.can_checkout_anywhere:
			return True

		def locations_within_radius(locations):
			for loc in locations:
				if self.coordinates_within_radius(
					curren_lat,
					current_lng,
					loc.latitude,
					loc.longitude,
					loc.permitted_radius):
					return True

		emp_locations = employee.permitted_attendance_locations
		if emp_locations:
			if locations_within_radius(emp_locations):
				return True
		emp_location_groups = employee.permitted_attendance_location_groups
		if emp_location_groups:
			for loc_group in emp_location_groups:
				if locations_within_radius(loc_group.locations):
					return True
		return False

	@http.route('/track_attendance', type='json', auth='api_key')
	def create_attendance(self, **data):
		# TD turn this into a punch function, and rename the URL
		if request.jsonrequest:
			time_now = datetime.now()
			try:
				local_timezone = self.is_valid(data.get('timeZone'), str)
				employee_id = self.is_valid(data.get('employee_id'), int)
				attendance_type = self.is_valid(data.get('attendance_type'), str)
				device_id = self.is_valid(data.get('device_id'), str)
				latitude = self.is_valid(data.get('lat'), float)
				longitude = self.is_valid(data.get('long'), float)
			except Exception as e:
				return self.Response(e, success=False)
			_logger.info(f"JSON Recevied {data}")

			employee_registrations = request.env['hr.attendance.appregistration'].sudo().search([
				('employee_id', '=', employee_id),
				('device_id', '=', device_id),
				])
			correctly_registered = bool(len(employee_registrations))
			if not correctly_registered:
				return self.Response(
					"This device is either not registered, or belongs to someone else. "
					"Or perhaps, the employee doesn't exist. Contact IT for help",
					success=False)
			
			if not self.is_employee_in_permitted_location(
				request,
				attendance_type,
				employee_id,
				latitude,
				longitude):
				return self.Response(
					"You're not allowed to check-in or out, outside of your workplace!",
					success=False)
			# TD get a more robust way of checking all scenarios
			open_checkins = request.env['hr.attendance'].search([
				('employee_id', '=', employee_id),
				('check_out', '=', None)
			])
			if attendance_type == 'check_in':
				try:
					if len(open_checkins):
						return self.Response(
							"You already have an open-checkin, therefore you need to checkout now. "
							"This is a server issue. Apologies for the inconvenience.",
							success=False)
					vals = {
						'employee_id': employee_id,
						'check_in': time_now
					}
					new_checkin = request.env['hr.attendance'].sudo().create(vals)
				except Exception as e:
					_logger.error('Error Raised')
					return self.Response(e, success=False)
				else:
					_logger.info(f'Result: {new_checkin}')
					return self.Response(
						'Checked In',
						employee_id=employee_id,
						attendance_id=new_checkin.id,
						time=self.set_time_to_users_timezone(time_now, local_timezone)
					)
			elif attendance_type == 'check_out':
				num_open_checkins = len(open_checkins)
				if num_open_checkins == 1:
					only_checkin_record = open_checkins[0]
					only_checkin_record['check_out'] = time_now
					attendance_id = only_checkin_record.id
					_logger.info('Registered Checkout!')
					return self.Response(
						'Checked Out',
						employee_id=employee_id,
						attendance_id=attendance_id,
						time=self.set_time_to_users_timezone(time_now, local_timezone)
					)
				elif num_open_checkins > 1:
					return self.Response(
						'There are too many open checkins, '
						'this is a server issue. Please contact your HR Manager.',
						success=False
					)
				else:
					return self.Response(
						"There are no open check-ins. We must have lost it! "
						"Proceed to checkin instead",
						success=False
					)
		return self.Response('Empty Response or Server Error', success=False)

	@http.route('/attendance/get_employee_state', type='json', auth='api_key')
	def get_attendance(self, **data):
		if request.jsonrequest:
			try: 
				employee_id = self.is_valid(data.get('employee_id'), int)
				device_id = self.is_valid(data.get('device_id'), str)
				local_timezone = self.is_valid(data.get('timeZone'), str)
			except Exception as e:
				return self.Response(e, success=False)
			_logger.info(f'JSON Received {data}')

			employee_registrations = request.env['hr.attendance.appregistration'].sudo().search([
				('employee_id', '=', employee_id),
				('device_id', '=', device_id),
				])
			correctly_registered = bool(len(employee_registrations))
			if not correctly_registered:
				return self.Response(
					"This device is either not registered, or belongs to someone else. "
					"Or perhaps, the employee doesn't exist. Contact IT for help",
					success=False)

			attendance_records = request.env['hr.attendance'].sudo().search([('employee_id', '=', employee_id),
																			('check_in', '!=', None)],
																	limit=5,
																	order='check_in desc')
			if len(attendance_records) == 0:
				return self.Response('No previous attendance history! Go ahead and check in')

			open_checkins = attendance_records.filtered(lambda rec: rec.check_out in [False, None])
			n_open_checkins = len(open_checkins)
			if n_open_checkins == 0:
				last_rec = attendance_records[0]
				checkout_time = self.set_time_to_users_timezone(last_rec['check_out'], local_timezone)
				return self.Response('Checked Out', state='check_out', time=checkout_time)
			elif n_open_checkins > 1:
				_logger.error(attendance_records)
				return self.Response("There are more than one open check-ins. "
									"This is a server issue. Please contact IT immediately!",
									success=False)
			else:
				last_rec = attendance_records[0]
				checkin_time = self.set_time_to_users_timezone(last_rec['check_in'], local_timezone)
				return self.Response('Checked In', state='check_in', time=checkin_time)

	@http.route('/attendance/is_device_registered', type='json', auth='api_key')
	def authenticate_device(self, **data):
		if request.jsonrequest:
			_logger.info(data)
			try:
				device_id = self.is_valid(data.get('device_id'), str)
			except Exception as e:
				return self.Response(e, success=False)
			
			found_devices = request.env['hr.attendance.appregistration'].sudo().search([('device_id', '=', device_id)])
			matched = bool(len(found_devices))
			if matched:
				device_record = found_devices[0]	
				employee_name = device_record.employee_id.name
				employee_id = device_record.employee_id_num
				return self.Response(True,
									data={
										'employee_id': employee_id,
										'employee_name': employee_name,
									})
			else: return self.Response(False)

	@http.route('/attendance/register', type='json', auth='api_key')
	def register(self, **data):
		if request.jsonrequest:
			_logger.info(data)
			try:
				employee_id = self.is_valid(data.get('employee_id'), int)
				passcode = self.is_valid(data.get('passcode'), str)
				device_id = self.is_valid(data.get('device_id'), str)
			except Exception as e:
				return self.Response(e, success=False)
			
			employees = request.env['hr.employee'].sudo().search([('id', '=', employee_id), ('active', '=', True)])
			employee_found = bool(len(employees))
			if not employee_found:
				return self.Response(
					"This Employee ID doesn't exist. Please check again.",
					success=False)

			devices = request.env['hr.attendance.appregistration'].sudo().search([('device_id', '=', device_id)])
			device_registered = bool(len(devices))
			if device_registered:
				device_registration = devices[0]
				if device_registration.employee_id.id == employee_id:
					return self.Response('You are already registered', success=False)
			if device_registered:
				return self.Response("This device is linked to another employee.")


			employee_registrations = request.env['hr.attendance.appregistration'].sudo().search([('employee_id', '=', employee_id)])
			employee_registered = bool(len(employee_registrations))
			if employee_registered:
				return self.Response(
					"You have already registered on a different device. "
					"If you're trying to register a new device, "
					"then please contact your HR manager.",
					success=False)
			
			stored_employee = employees[0]
			stored_passcode = stored_employee.pin
			if not stored_passcode:
				stored_employee.update({'pin': self.generate_passcode()})
				return self.Response(
					"Oops! Your passcode has not been generated before. "
					"Please collect it from IT. And register again.",
					success=False)
			if passcode != stored_passcode:
				return self.Response(
					"Your passcode is incorrect. Please collect it from IT & register again.",
					success=False)

			new_registration = {
				'employee_id': employee_id,
				'device_id': device_id,
			}
			request.env['hr.attendance.appregistration'].sudo().create(new_registration)
			return self.Response('Registration Successful',
								data={
									'employee_id': employee_id,
									'employee_name': stored_employee.name
									})
			