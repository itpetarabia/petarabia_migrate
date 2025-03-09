-- List of Product Internal-References
with products as (
    select p.id, p.barcode, tp.name
    from product_product p
    inner join product_template tp 
    on tp.id = p.product_tmpl_id
     AND p.available_on_instashop = True
     AND p.active = True -- TD need to assign products

),

prod_location as (
    select
        p.id,
        p.barcode,
        p.name,
        q.location_id,
        q.lot_id, --Can remove this later
        l.complete_name,
        -- incase the lot_serial qty is negative, it renders it as zero
        GREATEST(q.quantity - q.reserved_quantity, 0) qty
    from products p
    left join stock_quant q
    on q.product_id = p.id
        AND q.location_id in ({INSERT_LOCATION_IDS})
    left join stock_location l
    on q.location_id = l.id
    order by p.barcode
),

branch_products as (
    select
        id,
        barcode,
        name,
        location_id,
        complete_name,
        sum(qty) total_qty,
        (CASE 
            WHEN sum(qty)>0  THEN 'in_stock'
            ELSE 'disabled'
        END) status

    from prod_location 
    group by id, barcode, name, location_id, complete_name
)

SELECT
    id,
    name,
    barcode,
    array_agg(location_id) location_ids,
    array_agg(status) statuses,
    array_agg(total_qty) total_qty_list
from branch_products group by id, name, barcode;

-- # Get Locations for Each POS
-- select pos.id, pos.name, l.id location_id, l.complete_name location_name from pos_config pos
-- inner join stock_picking_type pt
-- on pos.picking_type_id = pt.id
-- inner join stock_warehouse w
-- on pt.warehouse_id = w.id
-- inner join stock_location l
-- on w.lot_stock_id = l.id