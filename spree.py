# https://github.com/spree/spree
# Note that in Rails, calling .touch on an ActiveRecord object triggers a DB update.
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

def spree_checkout_controller_generator():
    """
    Transaction 4.
    Validation-based transaction.
    Purpose: Coordinate concurrent checkout.
    app/controllers/spree/checkout_controller.rb:101
    
    https://github.com/spree/spree/blob/840041ef5747387d3752c4d0acf4e38ff8a35292/frontend/app/controllers/spree/checkout_controller.rb#L95-L107
    Mentioned by Project Concerto here https://github.com/spree/spree/issues/10733
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

    spree_adjustment_update_sim(num_txn_1) # Transaction 1

if __name__ == "__main__":
    main()