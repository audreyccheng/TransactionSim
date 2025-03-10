

class Transaction:
    """
    Utility class to represent transactions.

    Example usage:
    >>> t = Transaction()
    >>> print(t)
    []
    >>> t.append_read("cart0")
    >>> t.append_write("apple")
    >>> print(t)
    ['r-cart0', 'w-apple']
    >>> t.clear()
    >>> print(t)
    []
    """
    def __init__(self):
        """
        Initialize transaction trace, which is stored as a Python list.
        Every read/write call is added to this list which tracks the
        operations inside the transaction.
        """
        self.trace = []

    def __str__(self):
        """
        When printing a Transaction object, print self.trace.
        """
        return str(self.trace)

    def append_read(self, item: str):
        """
        Append a read to the current list of transaction operations.
        Stored as a "r-item" string where item is the argument to the
        method.
        """
        assert type(item) == str
        self.trace.append(f"r-{item}")

    def append_write(self, item: str):
        """
        Append a write to the current list of transaction operations.
        Stored as a "w-item" string where item is the argument to the
        method.
        """
        assert type(item) == str
        self.trace.append(f"w-{item}")

    def clear(self):
        """
        Reset the transaction trace to an empty list.
        """
        self.trace = []

    def get_trace(self) -> list[str]:
        """
        Return transaction trace.
        """
        return self.trace