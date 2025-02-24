import threading

from cartdb import *

class Order():
    VALID_OPERATIONS = ['r', 'w']
    ORDER_NUM = 0

    def __init__(self, transaction: list):
        self.transaction = transaction
        self.order_num = Order.ORDER_NUM
        self.lock = None
        Order.ORDER_NUM += 1

    def get_operations(self):
        return self.transaction

    def add_operation(self, instruction: str, val=None):
        assert instruction in Order.VALID_OPERATIONS, f"Incorrect operation type: \
            {instruction}. Type must be in {Order.VALID_OPERATIONS}"
        assert val == None or type(val) == str, f"Invalid value {val}"
        self.transaction.append((instruction, val))

    def pop_operation(self) -> tuple[str, str]:
        return self.transaction.pop()

    def flush_operations(self) -> list:
        temp = self.transaction
        self.transaction = []
        return temp
    
    def acquire_lock(self):
        """
        Currently does nothing.
        """
        return True

    def release_lock(self):
        """
        Currently does nothing.
        """
        return
    
def execute_order(database: CartDB, order: Order):
    """
    Simulate updating a cart as described in Broadleaf source code.
    """
    operations = order.get_operations()
    curr_cart = None
    for operation in operations:
        inst, val = operation
        if inst == 'r':
            curr_cart = database.get_cart(val)
        elif inst == 'w':
            assert type(curr_cart) == Cart, "Invalid transaction sequence"
            curr_cart.add_item(val)

def main():
    """
    This main function simulates Broadleaf transaction use case #1 as identified in my notes.
    """
    # Initialize a cart with cart_id 0 in the database.
    db = CartDB()
    cart_id = 0
    cart = Cart()
    db.add_cart_entry(cart_id, cart)

    # Create a transaction that adds 'apple' and 'bananna' to the cart
    new_item_1 = 'apple'
    new_item_2 = 'bananna'
    transaction = [('r', cart_id), ('w', new_item_1), ('w', new_item_2)]
    order = Order(transaction)

    # Simulate the transaction pattern used in Broadleaf example 1
    lock = None
    lock = order.acquire_lock()
    print(f"Contents of cart {cart_id}: {db.get_cart(cart_id).get_items()}")
    print(f"Thread [{threading.current_thread()}] grabbed lock for order {order.order_num}")
    print(f"The order currently consists of the following transaction: {order.transaction}")
    print(f"Now, we update the cart contents with the order.\n\nUpdating cart...\n")

    execute_order(db, order)

    order.release_lock()
    print(f"Thread [{threading.current_thread()}] released lock for order {order.order_num}")
    print(f"Contents of cart {cart_id} after processing the order: {db.get_cart(cart_id).get_items()}")

if __name__ == "__main__":
    main()
