

class Cart():
    """
    Represents a cart.
    """
    def __init__(self):
        self.items = []

    def get_items(self) -> list[str]:
        return self.items

    def add_item(self, item: str):
        self.items.append(item)

    def pop_item(self) -> str:
        return self.items.pop()

class CartDB():
    """
    Simple cart database which tracks customer's cart contents by cart_id.
    """
    def __init__(self):
        self.contents = {} # Map cart_id to Cart object

    def add_cart_entry(self, cart_id: str, cart: Cart):
        self.contents[cart_id] = cart

    def get_cart(self, cart_id: str) -> Cart:
        return self.contents[cart_id]



