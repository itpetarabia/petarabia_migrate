import requests
from functools import reduce

STANDARD_HEADERS = {
  'Content-Type': 'application/json'
}

class InstaConnector:
    def __init__(self, api_key, url):
        self.api_key = api_key
        self.baseurl = url
        self.login_url = f"{self.baseurl}/auth/login"
        self.token, _ = self.auth()


        self.headers = {'Authorization': f'Bearer {self.token}'}
        self.headers.update(STANDARD_HEADERS)
    
    @staticmethod
    def _check_response(res: dict):
        try:
            if not res.get('success'):
                raise Exception(res.get('message') or 'Unknown Error (No Message Provided)')
        except ValueError:
            return 'Unknown Error'

    def auth(self):
        payload = {'apiKey': self.api_key}
        res = requests.request("POST", self.login_url, headers=STANDARD_HEADERS, json=payload)
        res = res.json()
        self._check_response(res)
        return res['data']['token'], res['data']['identifiers']

    def post(self, uri, payload):
        url = f'{self.baseurl}{uri}'
        res = requests.request(
            "POST",
           url,
           headers=self.headers,
           json=payload)
        res = res.json()
        self._check_response(res)
        return res


    def products_status(self, list_of_prods, branch_id):
        payload = {
        'identifier': branch_id,
        'products' : list_of_prods ,
        } 
        return self.post('/products/status', payload)


    def update_products(self, branch_id, list_of_prods):
        payload = {
        'identifier': branch_id,
        'products' : list_of_prods,
       }
        return self.post('/products/update', payload)
    
    async def update_products_faster(self, session, branch_id, list_of_prods):
        # print(list_of_prods)
        uri = '/products/update'
        url = f'{self.baseurl}{uri}'
        async with session.post(url,
                        json=
                        {
                            'identifier': branch_id,
                            "products": list_of_prods,
                        },
                        headers=self.headers,
                        ) as resp:
            res = await resp.json()
            self._check_response(res)

        updated_prods = res['data']
        num_of_unmatched_prods = 0
        for prod in updated_prods:
            if prod['status'] == 'not_matched':
                num_of_unmatched_prods += 1
        return res, num_of_unmatched_prods
        



def SimpleBarcodeList(barcodes:list):
    """Converts a List of barcodes
      to a List of Json-compatible barcodes """
    return [{
        'plu': b,
        'barcode': b,
    } for b in barcodes]

def ExtBarcodeList(barcodes: list):
    """Converts a List of barcodes
    to a `Detailed` List of Json-compatible barcoes """
    return [{
        'plu': b[0],
        'barcode': b[0],
        'price': b[1],
        'discountPrice': b[2],
        'status': b[3],
    }
    for b in barcodes]

if __name__ == '__main__':
    baseurl = ""
    api_key =  ""
    conn = InstaConnector(api_key, baseurl)

    barcode = '635934607935'
    price = 3.4
    discount_price = 3.0
    status = 'in_stock'
    zallaq_branch_id = 'PetArabia-Zallaq'

    

    
    
    res = conn.update_products(zallaq_branch_id, ExtBarcodeList([(barcode, price, discount_price, status)]))
    print(res) 

    res = conn.products_status(SimpleBarcodeList([barcode]), zallaq_branch_id)
    print(res)
    
    
