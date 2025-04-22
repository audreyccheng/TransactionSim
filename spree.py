# https://github.com/spree/spree
# Note that in Rails, calling .touch on an ActiveRecord object triggers a DB update.
# Look for ActiveRecord::Base.transaction to find transaction blocks.
# Total of 10 transactions

import numpy as np
from transaction import Transaction

### Transaction 1 (Transaction 5 from Tang et al.) ###
def spree_adjustment_update_generator(adjustment: dict) -> list[str]:
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
        transaction = spree_adjustment_update_generator(adjustment)
        print(transaction)

### Transaction 2 (Transaction 4 from Tang et al.) ###
def spree_checkout_controller_generator(order_id: int, input_data: dict) -> list[str]:
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
def spree_fulfillment_changer_generator(order_id: int,
        variant_id: int,
        current_shipment_id: int,
        desired_shipment_id: int,
        current_stock_location_id: int,
        desired_stock_location_id: int,
        current_on_hand_quantity: int,
        restock_quantity: int,
        unstock_quantity: int,
        new_on_hand_quantity: int
    ) -> list[str]:
    """
    https://github.com/spree/spree/blob/249aa157ab33d94cffff779d66039c1b4580f6f4/core/app/models/spree/fulfilment_changer.rb#L41C5-L51C1
    
    PSEUDOCODE:
    In: current_stock_location, desired_stock_location, order, variant, shipment, 
        current_on_hand_quantity, unstock_quantity
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
    SELECT unit FROM inventory_units WHERE shipment_id = desired_shipment.id AND variant_id = variant.id
    if unit is null: -- this represents a find_or_create
        INSERT INTO inventory_units (shipment_id, variant_id, state) VALUES (desired_shipment.id, variant.id, 'on_hand')
    UPDATE inventory_units SET quantity = quantity + new_on_hand_quantity
        WHERE shipment_id = desired_shipment.id AND variant_id = variant.id AND state = 'on_hand'

    if current_on_hand_quantity > new_on_hand_quantity:
        UPDATE inventory_units SET quantity = quantity - (current_on_hand_quantity - new_on_hand_quantity)
        WHERE shipment_id = current_shipment.id AND variant_id = variant.id AND state = 'on_hand';
    if unit is null: -- this represents a find_or_create
        INSERT INTO inventory_units (shipment_id, variant_id, state) VALUES (desired_shipment.id, variant.id, 'backordered')
        UPDATE inventory_units SET quantity = quantity + new_backordered_quantity
            WHERE shipment_id = desired_shipment.id AND variant_id = variant.id AND state = 'backordered'

    -- part 2: update current shipment
    UPDATE inventory_units SET quantity_left = quantity - reduced_quantity WHERE state = 'backordered'
    if quantity_left > 0:
        UPDATE inventory_units SET quantity_left = quantity - reduced_quantity WHERE state = 'on_hand'

    TRANSACTION COMMIT
    """
    t = Transaction()

    # Read current quantity in current shipment
    t.append_read(f"inventory_units-shipment_id({current_shipment_id})-variant_id({variant_id})")

    # Conditionally update stock counts
    t.append_conditional("order.state == 'complete' AND current != desired")

    t.append_write(f"restock-stock_item-location({current_stock_location_id})-variant({variant_id})-qty(+{restock_quantity})")
    t.append_write(f"unstock-stock_item-location({desired_stock_location_id})-variant({variant_id})-qty(-{unstock_quantity})")

    # Desired shipment on_hand unit update
    t.append_find_or_create(f"inventory_unit-shipment({desired_shipment_id})-state('on_hand')-variant({variant_id})")
    t.append_write(f"update-inventory_unit-qty(+{new_on_hand_quantity})")

    # Desired shipment backordered update (if needed)
    backorder_qty = current_on_hand_quantity - new_on_hand_quantity
    if backorder_qty > 0:
        t.append_find_or_create(f"inventory_unit-shipment({desired_shipment_id})-state('backordered')-variant({variant_id})")
        t.append_write(f"update-inventory_unit-qty(+{backorder_qty})")

    # Reduce current shipment units
    t.append_iterate("inventory_units", f"shipment({current_shipment_id})-variant({variant_id})")

    t.append_conditional("unit.quantity > reduced_quantity")
    t.append_write("unit.quantity -= reduced_quantity")

    t.append_else()
    t.append_delete("inventory_unit")

    return t

### Other Transactions

def spree_find_order_by_token_or_user_generator():
    """
    Transaction 1.
    Lock-based transaction.
    Purpose: Coordinate concurrent checkout.
    Spree::Core::ControllerHelpers::Order#find_order_by_token_or_user

    https://github.com/spree/spree/blob/09e8024d8742c6f0b8bd5ee266e3e25a65d66523/core/lib/spree/core/controller_helpers/order.rb#L133
    PSEUDOCODE:
    In:
    TRANSACTION START
    TRANSACTION COMMIT
    """

def spree_handle_action_call_generator():
    """
    Transaction 2.
    Lock-based transaction.
    Purpose: Coordinate concurrent checkout.
    Spree::PaymentMethod::StoreCredit#handle_action_call

    https://github.com/spree/spree/blob/09e8024d8742c6f0b8bd5ee266e3e25a65d66523/core/app/models/spree/payment_method/store_credit.rb#L110
    PSEUDOCODE:
    In:
    TRANSACTION START
    TRANSACTION COMMIT
    """


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

def spree_stock_item_update_generator():
    """
    Transaction 10.
    Lock-based transaction.
    Purpose: Coordinate concurrent stock updating
    app/models/spree/stock_item.rb:37

    adjust_count_on_hand
    https://github.com/spree/spree/blob/840041ef5747387d3752c4d0acf4e38ff8a35292/core/app/models/spree/stock_item.rb#L37
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

def main():
    """
    Generate Spree transaction traces.
    """
    # Number of transactions to simulate per transaction type
    num_txn_1 = 10
    num_txn_2 = 10

    # spree_adjustment_update_sim(num_txn_1) # Transaction 1
    spree_checkout_controller_sim(num_txn_2) # Transaction 2

if __name__ == "__main__":
    main()
