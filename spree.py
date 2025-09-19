# https://github.com/spree/spree
# Note that in Rails, calling .touch on an ActiveRecord object triggers a DB update.
# Look for ActiveRecord::Base.transaction to find transaction blocks.
# Total of 10 transactions

import numpy as np
from transaction import Transaction

class Order:
    def __init__(self):
        self.order_id = np.random.randint(1, 100)
        self.variant_id = np.random.randint(1, 50)
        self.quantity = np.random.randint(1, 10)

class LineItem:
    def __init__(self):
        self.id = np.random.randint(1, 50)
        self.quantity = np.random.randint(1, 10)
        self.exists: bool = np.random.binomial(1, 0.9) 

class StockItem:
    def __init__(self):
        self.id = np.random.randint(1, 500)
        self.count_on_hand = np.random.randint(0, 10) # We assume count_on_hand is relatively small otherwise BackorderedUnit would already be fulfilled 

class BackorderedUnit:
    def __init__(self, quantity = np.random.randint(1, 10)):
        self.id = np.random.randint(1, 500)
        self.quantity = quantity

### Transaction 1 (Transaction 5 from Tang et al.) ###
def spree_adjustment_update_generator(adjustment: dict) -> Transaction:
    """
    Validation-based transaction.
    Purpose: Coordinate concurrent checkout.
    app/models/spree/adjustment.rb:104

    update! function
    https://github.com/spree/spree/blob/8980e2ac9c9c5385c795dee08992cdd1fa2e2f18/core/app/models/spree/adjustment.rb#L98-L109
    PSEUDOCODE:
    In: adjustment{id, state, source_id, source_type}
    TRANSACTION START
        IF adjustment is closed OR has no source:
            Return current amount
        UPDATE adjustments SET amount, updated_at [, eligible] WHERE id = adjustment.id
        IF promotion: 
            UPDATE promotions SET updated_at WHERE id = source.promotion_id
    TRANSACTION COMMIT
    """
    t = Transaction()

    # Read lock on the adjustment
    t.append_read(f"adjustment-id({adjustment['id']})")

    if adjustment["state"] == "closed" or not adjustment.get("source_id"):
        return t

    fields_to_update = ["amount", "updated_at"]
    if adjustment.get("source_type") == "Spree::PromotionAction":
        fields_to_update.append("eligible")
        t.append_write(f"promotion-id({adjustment['source_id']})-fields({fields_to_update})")

    t.append_write(f"adjustment-id({adjustment['id']})")

    return t

def spree_adjustment_update_sim(num_txn: int):
    """
    Example output:
    
    ['r-adjustment-id(37)', "w-promotion-id(70)-fields(['amount', 'updated_at', 'eligible'])", 'w-adjustment-id(37)']
    ['r-adjustment-id(23)']
    ['r-adjustment-id(95)', "w-promotion-id(33)-fields(['amount', 'updated_at', 'eligible'])", 'w-adjustment-id(95)']
    ['r-adjustment-id(96)', 'w-adjustment-id(96)']
    ['r-adjustment-id(65)', "w-promotion-id(28)-fields(['amount', 'updated_at', 'eligible'])", 'w-adjustment-id(65)']
    ['r-adjustment-id(26)']
    ['r-adjustment-id(69)']
    ['r-adjustment-id(80)']
    ['r-adjustment-id(2)', "w-promotion-id(55)-fields(['amount', 'updated_at', 'eligible'])", 'w-adjustment-id(2)']
    ['r-adjustment-id(52)', 'w-adjustment-id(52)']
    """
    for _ in range(num_txn):
        source_id = np.random.randint(1, 100)
        if np.random.rand() < 0.2:
            source_id = None
        adjustment = {
            "id": np.random.randint(1, 100),
            "state": np.random.choice(["open", "closed"], p=[0.7, 0.3]),
            "source_id": source_id,
            "source_type": np.random.choice(["Spree::PromotionAction", "OtherType"], p=[0.3, 0.7])
        }
        result = spree_adjustment_update_generator(adjustment)
        print(result)

### Transaction 2 (Transaction 4 from Tang et al.) ###
def spree_checkout_controller_generator(order_id: int, input_data: dict) -> Transaction:
    """
    Transaction 4.
    Validation-based transaction.
    Purpose: Coordinate concurrent checkout.
    app/controllers/spree/checkout_controller.rb:101

    https://github.com/spree/spree/blob/a436948268d2626ed1bc8304d1a40e3f5b792992/storefront/spec/controllers/spree/checkout_controller_spec.rb#L641C7-L697C8
    PSEUDOCODE:
    In: state_lock_version
    TRANSACTION START

    SELECT state_lock_version FROM orders FOR UPDATE;

    IF input.state_lock_version == db.state_lock_version THEN
        UPDATE orders SET ship_address = {...}, 
        last_ip_address = '0.0.0.0', 
        state_lock_version = state_lock_version + 1  -- Increment the version to indicate update

    TRANSACTION COMMIT
    """

    t = Transaction()
    
    t.append_read(f"lock_version-order_id({order_id})")  # Read current lock version
    input_version = input_data["state_lock_version"]

    # Only perform the update if the state_lock_version matches
    if input_version == 1: # Simulate a successful update
        t.append_write(f"order({order_id})")  # Write ship address
        t.append_write("last_ip_addr(0.0.0.0)")  # Write last_ip_address
        t.append_write(f"lock_version({1})")  # Set lock_version to 1

    return t

def spree_checkout_controller_sim(num_txn: int):
    """
    Example output:

    ['r-lock_version-order_id(47)', 'w-order(47)', 'w-last_ip_addr(0.0.0.0)', 'w-lock_version(1)']
    ['r-lock_version-order_id(29)', 'w-order(29)', 'w-last_ip_addr(0.0.0.0)', 'w-lock_version(1)']
    ['r-lock_version-order_id(48)']
    ['r-lock_version-order_id(54)', 'w-order(54)', 'w-last_ip_addr(0.0.0.0)', 'w-lock_version(1)']
    ['r-lock_version-order_id(75)', 'w-order(75)', 'w-last_ip_addr(0.0.0.0)', 'w-lock_version(1)']
    ['r-lock_version-order_id(26)', 'w-order(26)', 'w-last_ip_addr(0.0.0.0)', 'w-lock_version(1)']
    ['r-lock_version-order_id(57)', 'w-order(57)', 'w-last_ip_addr(0.0.0.0)', 'w-lock_version(1)']
    ['r-lock_version-order_id(17)', 'w-order(17)', 'w-last_ip_addr(0.0.0.0)', 'w-lock_version(1)']
    ['r-lock_version-order_id(16)', 'w-order(16)', 'w-last_ip_addr(0.0.0.0)', 'w-lock_version(1)']
    ['r-lock_version-order_id(13)']
    """
    for _ in range(num_txn):
        order_id = np.random.randint(1, 100)
        input_data = {
            "state_lock_version": np.random.binomial(1, 0.8)
        }
        result = spree_checkout_controller_generator(order_id, input_data)
        print(result)

### Transaction 3 ###
def spree_fulfillment_changer_generator(
        current_shipment_id: int,
        desired_shipment_id: int,
        current_stock_location_id: int,
        desired_stock_location_id: int,
        current_on_hand_quantity: int,
        unstock_quantity: int,
        new_on_hand_quantity: int,
        order_state: str,
        p: float,
    ) -> Transaction:
    """
    https://github.com/spree/spree/blob/249aa157ab33d94cffff779d66039c1b4580f6f4/core/app/models/spree/fulfilment_changer.rb#L41C5-L51C1
    
    PSEUDOCODE:
    In: current_shipment_id, desired_shipment_id, current_stock_location, desired_stock_location, 
        current_on_hand_quantity, unstock_quantity, new_on_hand_quantity, order_state, p
    TRANSACTION START

    SELECT SUM(quantity) FROM inventory_units WHERE shipment_id = current_shipment.id AND variant_id = variant.id
    AND state IN ('on_hand', 'backordered');

    IF order.state = 'complete' AND current_stock_location.id != desired_stock_location.id
        -- restock
        UPDATE stock_items SET count_on_hand = count_on_hand + restock_quantity WHERE stock_location_id = current_stock_location.id AND variant_id = variant.id

        -- unstock
        UPDATE stock_items SET count_on_hand = count_on_hand - unstock_quantity WHERE stock_location_id = desired_stock_location.id AND variant_id = variant.id

    -- move inventory units between shipments
    -- part 1: update desired shipment
    SELECT unit FROM inventory_units WHERE shipment_id = desired_shipment.id AND variant_id = variant.id AND state = 'on_hand'
    if unit is null: -- this represents a find_or_create
        INSERT INTO inventory_units (shipment_id, variant_id, state) VALUES (desired_shipment.id, variant.id, 'on_hand')
    UPDATE inventory_units SET quantity = quantity + new_on_hand_quantity
        WHERE shipment_id = desired_shipment.id AND variant_id = variant.id AND state = 'on_hand'

    if current_on_hand_quantity > new_on_hand_quantity:
        SELECT unit FROM inventory_units WHERE shipment_id = desired_shipment.id AND variant_id = variant.id AND state = 'backordered
        if unit is null: -- this represents a find_or_create
            INSERT INTO inventory_units (shipment_id, variant_id, state) VALUES (desired_shipment.id, variant.id, 'backordered')
        UPDATE inventory_units SET quantity = quantity + new_backordered_quantity
            WHERE shipment_id = desired_shipment.id AND variant_id = variant.id AND state = 'backordered'

    -- part 2: update current shipment
    UPDATE inventory_units SET quantity_left = current_on_hand_quantity - backorder_qty WHERE state = 'backordered'
    if quantity_left > 0:
        UPDATE inventory_units SET quantity_left = quantity - on_hand_qty WHERE state = 'on_hand'

    TRANSACTION COMMIT
    """
    t = Transaction()

    # Read current quantity in current shipment
    t.append_read(f"shipment_id-backordered({current_shipment_id})")

    # Conditionally update stock counts
    if order_state == "complete" and current_stock_location_id != desired_stock_location_id:
        t.append_write(f"restock_current_quantity({current_on_hand_quantity})")
        t.append_write(f"unstock_desired_quantity({unstock_quantity})")

    # Desired shipment on_hand unit update
    if p > 0.5: # Simulate a find_or_create
        t.append_read(f"on_hand_unit-shipment({desired_shipment_id})")
    else:
        t.append_write(f"on_hand_unit-shipment({desired_shipment_id})")
    t.append_write(f"add_on_hand_quantity({new_on_hand_quantity})")

    # Desired shipment backordered update (if needed)
    backorder_qty = current_on_hand_quantity - new_on_hand_quantity
    if backorder_qty > 0:
        if p > 0.5: # Simulate a find_or_create
            t.append_read(f"backordered_unit-shipment({desired_shipment_id})")
        else:
            t.append_write(f"backordered_unit-shipment({desired_shipment_id})")
        t.append_write(f"add_backordered_quantity({backorder_qty})")

    # Reduce current shipment units
    quantity_left = current_on_hand_quantity - backorder_qty
    t.append_write(f"reduce_backordered_quantity({backorder_qty})")
    if quantity_left > 0:
        t.append_write(f"reduce_on_hand_quantity({new_on_hand_quantity})")

    return t

def spree_fulfillment_changer_sim(num_txn: int):
    """
    Example output:

    ['r-shipment_id-backordered(40)', 'r-on_hand_unit-shipment(25)', 'w-add_on_hand_quantity(96)', 'w-reduce_backordered_quantity(-39)', 'w-reduce_on_hand_quantity(96)']
    ['r-shipment_id-backordered(30)', 'r-on_hand_unit-shipment(96)', 'w-add_on_hand_quantity(30)', 'r-backordered_unit-shipment(96)', 'w-add_backordered_quantity(69)', 'w-reduce_backordered_quantity(69)', 'w-reduce_on_hand_quantity(30)']
    ['r-shipment_id-backordered(36)', 'w-restock_current_quantity(3)', 'w-unstock_desired_quantity(96)', 'r-on_hand_unit-shipment(56)', 'w-add_on_hand_quantity(18)', 'w-reduce_backordered_quantity(-15)', 'w-reduce_on_hand_quantity(18)']
    ['r-shipment_id-backordered(36)', 'w-restock_current_quantity(71)', 'w-unstock_desired_quantity(60)', 'w-on_hand_unit-shipment(48)', 'w-add_on_hand_quantity(54)', 'w-backordered_unit-shipment(48)', 'w-add_backordered_quantity(17)', 'w-reduce_backordered_quantity(17)', 'w-reduce_on_hand_quantity(54)']
    ['r-shipment_id-backordered(85)', 'r-on_hand_unit-shipment(35)', 'w-add_on_hand_quantity(39)', 'r-backordered_unit-shipment(35)', 'w-add_backordered_quantity(38)', 'w-reduce_backordered_quantity(38)', 'w-reduce_on_hand_quantity(39)']
    ['r-shipment_id-backordered(36)', 'w-on_hand_unit-shipment(42)', 'w-add_on_hand_quantity(35)', 'w-reduce_backordered_quantity(-6)', 'w-reduce_on_hand_quantity(35)']
    ['r-shipment_id-backordered(49)', 'w-restock_current_quantity(77)', 'w-unstock_desired_quantity(90)', 'w-on_hand_unit-shipment(11)', 'w-add_on_hand_quantity(2)', 'w-backordered_unit-shipment(11)', 'w-add_backordered_quantity(75)', 'w-reduce_backordered_quantity(75)', 'w-reduce_on_hand_quantity(2)']
    ['r-shipment_id-backordered(14)', 'w-on_hand_unit-shipment(92)', 'w-add_on_hand_quantity(7)', 'w-backordered_unit-shipment(92)', 'w-add_backordered_quantity(35)', 'w-reduce_backordered_quantity(35)', 'w-reduce_on_hand_quantity(7)']
    ['r-shipment_id-backordered(63)', 'w-on_hand_unit-shipment(39)', 'w-add_on_hand_quantity(33)', 'w-reduce_backordered_quantity(-5)', 'w-reduce_on_hand_quantity(33)']
    ['r-shipment_id-backordered(59)', 'w-restock_current_quantity(17)', 'w-unstock_desired_quantity(74)', 'r-on_hand_unit-shipment(36)', 'w-add_on_hand_quantity(20)', 'w-reduce_backordered_quantity(-3)', 'w-reduce_on_hand_quantity(20)']
    """
    for _ in range(num_txn):
        current_shipment_id = np.random.randint(1, 100)
        desired_shipment_id = np.random.randint(1, 100)
        current_stock_location_id = np.random.randint(1, 100)
        desired_stock_location_id = np.random.randint(1, 100)
        current_on_hand_quantity = np.random.randint(1, 100)
        unstock_quantity = np.random.randint(1, 100)
        new_on_hand_quantity = np.random.randint(1, 100)
        order_state = np.random.choice(["complete", "incomplete"], p=[0.5, 0.5])
        p = np.random.rand()

        result = spree_fulfillment_changer_generator(
            current_shipment_id,
            desired_shipment_id,
            current_stock_location_id,
            desired_stock_location_id,
            current_on_hand_quantity,
            unstock_quantity,
            new_on_hand_quantity,
            order_state,
            p,
        )
        print(result)

### Transaction 4 ###
def spree_remove_line_item_generator(order: Order, line_item: LineItem) -> Transaction:
    """
    https://github.com/spree/spree/blob/249aa157ab33d94cffff779d66039c1b4580f6f4/core/app/services/spree/cart/remove_item.rb#L10
    remove_from_line_item

    PSEUDOCODE:
    In: 
    TRANSACTION START

    SELECT * FROM line_items WHERE order_id = order.id AND variant_id = variant.id

    IF line_item == null:
        TRANSACTION COMMIT

    if line_item.quantity - quantity <= 0:
        DELETE FROM line_items WHERE id = line_item.id;
    else:
        UPDATE line_items SET quantitline_item.quaantity = line_item.quantity - quantity WHERE id = line_item.id

    TRANSACTION COMMIT
    """
    t = Transaction()

    # Read lock on the line item
    t.append_read(f"order_id-variant_id({order.order_id, order.variant_id})")

    # Commit transaction if line item does not exist
    if not line_item.exists:
        return t 

    # Check if new quantity is <= 0
    if line_item.quantity - order.quantity <= 0:
        t.append_write(f"delete-line_item-id({line_item.id})")
    else:
        t.append_write(f"update-line_item-id({line_item.id})")

    return t

def spree_remove_line_item_sim(num_txn: int):
    """
    Example output:
    ['r-order_id-variant_id((9, 40))', 'w-delete-line_item-id(48)']
    ['r-order_id-variant_id((46, 36))', 'w-update-line_item-id(37)']
    ['r-order_id-variant_id((5, 20))', 'w-update-line_item-id(44)']
    ['r-order_id-variant_id((1, 23))', 'w-delete-line_item-id(25)']
    ['r-order_id-variant_id((43, 33))', 'w-delete-line_item-id(2)']
    ['r-order_id-variant_id((2, 30))', 'w-update-line_item-id(8)']
    ['r-order_id-variant_id((44, 49))', 'w-delete-line_item-id(45)']
    ['r-order_id-variant_id((38, 2))', 'w-delete-line_item-id(38)']
    ['r-order_id-variant_id((33, 48))', 'w-delete-line_item-id(49)']
    ['r-order_id-variant_id((27, 27))']

    """
    for _ in range(num_txn):
        order = Order()
        line_item = LineItem()
        result = spree_remove_line_item_generator(order, line_item)
        print(result)

### Transaction 5 (Transaction 10 from Tang et al.) ###
def spree_stock_item_update_generator(value: int, stock_item: StockItem, backordered_units: list[BackorderedUnit]) -> Transaction:
    """
    Transaction 10.
    Lock-based transaction.
    Purpose: Coordinate concurrent stock updating
    app/models/spree/stock_item.rb:37

    adjust_count_on_hand
    https://github.com/spree/spree/blob/840041ef5747387d3752c4d0acf4e38ff8a35292/core/app/models/spree/stock_item.rb#L37
    PSEUDOCODE:
    In: value, stock_item, backordered_units
    TRANSACTION START

    SELECT * FROM stock_items WHERE id = stock_item.id FOR UPDATE
    new_count = stock_item.count_on_hand + value
    orders_to_process = value
    
    if orders_to_process <= 0: 
        TRANSACTION COMMIT

    SELECT * FROM inventory_units WHERE stock_item_id = stock_item.id AND state = 'backordered' ORDER BY created_at ASC LIMIT difference;

    for backordered_unit in backordered_units:
        if orders_to_process <= 0:
            TRANSACTION COMMIT

        if backordered_unit.quantity > orders_to_process:
            -- Split the backordered unit into two units
            INSERT INTO inventory_units VALUES quantity = orders_to_process, id = split_unit.id
            UPDATE inventory_units SET quantity = quantity - orders_to_process WHERE id = backordered_unit.id

            UPDATE inventory_units SET state = 'fulfilled' WHERE id = split_unit.id
        else:
            UPDATE inventory_units SET state = 'fulfilled' WHERE id = backordered_unit.id
        orders_to_process = orders_to_process - backordered_unit.quantity

    UPDATE stock_items SET count_on_hand = new_count WHERE id = stock_item.id

    TRANSACTION COMMIT
    """
    t = Transaction()

    # Read the stock item
    t.append_read(f"stock_item_id, count_on_hand({stock_item.id, stock_item.count_on_hand})")
    new_count = stock_item.count_on_hand + value
    orders_to_process = value

    if orders_to_process <= 0:
        return t
    
    # Read backordered units
    t.append_read(f"backordered_units_num({len(backordered_units)})")
    
    for backordered_unit in backordered_units:
        if orders_to_process <= 0:
            return t

        if backordered_unit.quantity > orders_to_process:
            # Simulate splitting the backordered unit
            split_unit = BackorderedUnit(backordered_unit.quantity)
            t.append_write(f"split_unit_id({split_unit.id})")
            t.append_write(f"backordered_unit_new_count({backordered_unit.quantity - orders_to_process})") # Update quantity on backordered unit
            t.append_write(f"fulfilled_split_unit_count({split_unit.quantity})")
        else:
            t.append_write(f"fulfilled_backordered_unit_count({backordered_unit.quantity})")

        orders_to_process -= backordered_unit.quantity

    # Update the stock item count
    t.append_write(f"stock_item_new_count({new_count})")

    return t

def spree_stock_item_update_sim(num_txn: int):
    """
    Example output:

    ['r-stock_item_id, count_on_hand((487, 8))', 'r-backordered_units_num(1)', 'w-fulfilled_backordered_unit_count(3)', 'w-stock_item_new_count(82)']
    ['r-stock_item_id, count_on_hand((252, 1))', 'r-backordered_units_num(4)', 'w-fulfilled_backordered_unit_count(3)', 'w-split_unit_id(333)', 'w-backordered_unit_new_count(2)', 'w-fulfilled_split_unit_count(3)']
    ['r-stock_item_id, count_on_hand((306, 2))', 'r-backordered_units_num(1)', 'w-fulfilled_backordered_unit_count(3)', 'w-stock_item_new_count(39)']
    ['r-stock_item_id, count_on_hand((169, 4))', 'r-backordered_units_num(1)', 'w-fulfilled_backordered_unit_count(3)', 'w-stock_item_new_count(23)']
    ['r-stock_item_id, count_on_hand((290, 3))', 'r-backordered_units_num(0)', 'w-stock_item_new_count(33)']
    ['r-stock_item_id, count_on_hand((97, 4))', 'r-backordered_units_num(0)', 'w-stock_item_new_count(74)']
    ['r-stock_item_id, count_on_hand((313, 4))', 'r-backordered_units_num(2)', 'w-fulfilled_backordered_unit_count(3)', 'w-fulfilled_backordered_unit_count(3)', 'w-stock_item_new_count(71)']
    ['r-stock_item_id, count_on_hand((267, 2))', 'r-backordered_units_num(4)', 'w-fulfilled_backordered_unit_count(3)', 'w-fulfilled_backordered_unit_count(3)', 'w-fulfilled_backordered_unit_count(3)', 'w-fulfilled_backordered_unit_count(3)', 'w-stock_item_new_count(14)']
    ['r-stock_item_id, count_on_hand((264, 2))', 'r-backordered_units_num(2)', 'w-fulfilled_backordered_unit_count(3)', 'w-fulfilled_backordered_unit_count(3)', 'w-stock_item_new_count(24)']
    ['r-stock_item_id, count_on_hand((40, 6))', 'r-backordered_units_num(4)', 'w-fulfilled_backordered_unit_count(3)', 'w-fulfilled_backordered_unit_count(3)', 'w-fulfilled_backordered_unit_count(3)', 'w-fulfilled_backordered_unit_count(3)', 'w-stock_item_new_count(69)']
    """
    for _ in range(num_txn):
        value = np.random.randint(0, 100)
        stock_item = StockItem()
        backordered_units = [BackorderedUnit() for _ in range(np.random.randint(0, 5))]
        result = spree_stock_item_update_generator(value, stock_item, backordered_units)
        print(result)


### Other Transactions 
# Note: had a tough time finding the transactions for these code snippets.

def spree_ensure_sufficient_stock_lines_generator():
    """
    Transaction 7.
    Validation-based transaction.
    Purpose: Coordinate concurrent stock updating
    app/controllers/spree/checkout_controller.rb:18#ensure_sufficient_stock_lines
    
    https://github.com/spree/spree/blob/840041ef5747387d3752c4d0acf4e38ff8a35292/frontend/app/controllers/spree/checkout_controller.rb#L124
    PSEUDOCODE:
    In:
    TRANSACTION START
    TRANSACTION COMMIT
    """

def spree_line_item_variants_not_discontinued_generator():
    """
    Transaction 8.
    Validation-based transaction.
    Purpose: Coordinate concurrent goods status accessing
    app/models/spree/order.rb:400#ensure_line_item_variants_are_not_discontinued
    
    https://github.com/spree/spree/blob/840041ef5747387d3752c4d0acf4e38ff8a35292/core/app/models/spree/order.rb#L392
    PSEUDOCODE:
    In:
    TRANSACTION START
    TRANSACTION COMMIT
    """

def spree_line_items_in_stock_generator():
    """
    Transaction 9.
    Validation-based transaction.
    Purpose: Coordinate concurrent stock updating
    app/models/spree/order.rb:413#ensure_line_items_are_in_stock
    
    https://github.com/spree/spree/blob/840041ef5747387d3752c4d0acf4e38ff8a35292/core/app/models/spree/order.rb#L402
    PSEUDOCODE:
    In:
    TRANSACTION START
    TRANSACTION COMMIT
    """

# Skipping, cannot find in code
def spree_find_order_generator():
    """
    Transaction 3.
    Lock-based transaction.
    Purpose: Coordinate concurrent checkout.
    Spree::Api::V1::OrdersController#find_order
    """

# Skipping, cannot find in code
def spree_stock_item_checkout_generator():
    """
    Transaction 6.
    Validation-based transaction.
    Purpose: Coordinate concurrent checkout.
    app/models/spree/stock_item.rb:14
    """

# Skipping, after further investigation, these transactions do not involve contention
def spree_find_order_by_token_or_user_generator():
    """
    Transaction 1.
    Lock-based transaction.
    Purpose: Coordinate concurrent checkout.
    Spree::Core::ControllerHelpers::Order#find_order_by_token_or_user
    Note: find_order_by_token_or_user is called by current_order but that is not a transactio
    
    https://github.com/spree/spree/blob/09e8024d8742c6f0b8bd5ee266e3e25a65d66523/core/lib/spree/core/controller_helpers/order.rb#L133
    PSEUDOCODE:
    In: order_token, current_user
    TRANSACTION START

    if order_token == null or current_user == null:
        TRANSACTION COMMIT
    
    if adjustments:
        SELECT * FROM orders WHERE order_id = current_user.id AND state != 'complete' FOR UPDATE;
    else:
        SELECT * FROM orders WHERE order_id = current_user.id AND state != 'complete' FOR UPDATE;
        
    incomplete_orders = SELECT * FROM orders WHERE user_id = current_user.id AND state != 'complete' FOR UPDATE;

    TRANSACTION COMMIT
    """

# Skipping, could not find StoreCredit call event in codebase
def spree_handle_action_call_generator():
    """
    Transaction 2.
    Lock-based transaction.
    Purpose: Coordinate concurrent checkout.
    Spree::PaymentMethod::StoreCredit#handle_action_call
    Note: possible actions are capture, void, credit, and cancel. Cannot find the call events for these actions.

    https://github.com/spree/spree/blob/09e8024d8742c6f0b8bd5ee266e3e25a65d66523/core/app/models/spree/payment_method/store_credit.rb#L110
    PSEUDOCODE:
    In:
    TRANSACTION START
    TRANSACTION COMMIT
    """

def main():
    """
    Generate Spree transaction traces.
    """
    # Number of transactions to simulate per transaction type
    num_txn_1 = 10
    num_txn_2 = 10
    num_txn_3 = 10
    num_txn_4 = 10
    num_txn_5 = 10

    # spree_adjustment_update_sim(num_txn_1) # Transaction 1
    # spree_checkout_controller_sim(num_txn_2) # Transaction 2
    # spree_fulfillment_changer_sim(num_txn_3) # Transaction 3
    # spree_remove_line_item_sim(num_txn_4) # Transaction 4
    spree_stock_item_update_sim(num_txn_5) # Transaction 5

if __name__ == "__main__":
    main()
