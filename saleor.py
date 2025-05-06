# https://github.com/saleor/saleor
# Uses PostgreSQL
# Found in Tang et al. Ad Hoc Transactions in Web Applications: The Good, the Bad, and the Ugly

# Contextual note: select_for_update is used to lock rows until the end of the transaction. 
# Django docs: https://docs.djangoproject.com/en/5.1/ref/models/querysets/#select-for-update 

import numpy as np
import datetime
from transaction import Transaction

class Voucher: 
    def __init__(self):
        self.is_voucher_usage_increased: bool = np.random.binomial(1, 0.5)
        self.usage_limit: int = int(np.random.normal(5, 1))
        self.apply_once_per_customer: bool = np.random.binomial(1, 0.5)
        self.single_use: bool = np.random.binomial(1, 0.5)
        self.exists: bool = np.random.binomial(1, 0.5)

class Code:
    def __init__(self):
        voucher_ids = list(range(100))
        self.used: int = np.random.choice(range(10))
        self.is_active: bool = np.random.binomial(1, 0.5)
        self.voucher_id: int = np.random.choice(voucher_ids)

class Payment:
    def __init__(self):
        self.pk: int = np.random.choice(range(100))
        self.id: int = self.pk
        self.to_confirm: bool = np.random.binomial(1, 0.5)
        self.is_active: bool = np.random.binomial(1, 0.8)
        self.can_refund: bool = np.random.binomial(1, 0.5)
        self.can_void: bool = np.random.binomial(1, 0.5)
        self.order_id: int = np.random.choice(range(100))
        
class Checkout:
    def __init__(self):
        self.id: int = np.random.choice(range(100))
        self.is_voucher_usage_increased: bool = np.random.binomial(1, 0.5)
        self.completing_started_at: datetime.datetime = np.random.choice([datetime.datetime.now(), None])
        self.exists: bool = np.random.binomial(1, 0.9)

class StripePaymentObj:
    def __init__(self):
        self.payment_intent_id: int = np.random.choice(range(100))
        self.payment_active: bool = np.random.binomial(1, 0.5)
        self.payment_order_exists: bool = np.random.binomial(1, 0.5)
        self.payment_charge_status_pending: bool = np.random.binomial(1, 0.5)
        self.checkout_exists: bool = np.random.binomial(1, 0.5)
        self.payment_amount: int = np.random.choice(range(100))
        self.payment_currency: str = np.random.choice(["USD", "EUR", "GBP"])

class Fulfillment:
    def __init__(self):
        num_lines = np.random.choice(range(1, 10))
        self.lines = [FulfillmentLine() for _ in range(num_lines)]
        self.warehouse = np.random.choice(range(100))

class FulfillmentLine:
    def __init__(self):
        self.order_line = OrderLine()
        self.pk = np.random.choice(range(100))

class OrderLine:
    def __init__(self):
        self.variant: bool = np.random.binomial(1, 0.5)
        self.track_inventory: bool = np.random.binomial(1, 0.5)
        self.pk = np.random.choice(range(100))

class Order:
    def __init__(self, order_pk: int):
        self.pk: int = order_pk
        self.payment: Payment = Payment()
        self.status: str = "pending"
        self.exists: bool = np.random.binomial(1, 0.5)

class SaleorTransaction: 
    def __init__(self):
        self.kind: str = np.random.choice(["ACTION_TO_CONFIRM", "CAPTURE", "REFUND", "VOID"])
        self.pk: int = np.random.choice(range(100))

class Site:
    def __init__(self):
        self.pk: int = np.random.choice(range(100))

#################################
####   Simulator functions   ####
#################################

### Transaction 1 (Transaction 1 from Tang et al.) ###
def saleor_checkout_voucher_code_generator(voucher_code: int) -> list[str]:
    """
    Purpose: Coordinate concurrent checkout.
    saleor/checkout/complete_checkout.py#complete_checkout(with voucher code usage)
    
    Focusing on _increase_voucher_code_usage_value
    https://github.com/saleor/saleor/blob/c0423c3cd4968b287d71896d086e03483ac196d1/saleor/checkout/complete_checkout.py#L1498
    PSEUDOCODE: 
    In: checkout_info
    TRANSACTION START
    ** get_voucher_for_checkout part
    if checkout_info.voucher_code is not None:
        code = Select * from voucher_codes where code=checkout_info.voucher_code and is_active=True
        if code DNE: TRANSACTION COMMIT
        if checkout_info.is_voucher_usage_increased:
            voucher = Select * from vouchers where id=code.voucher_id LIMIT 1
        else:
            voucher = Select * from vouchers where id=code.voucher_id and active_in_channel=checkout_info.channel_id LIMIT 1????
    
    if not voucher: TRANSACTION COMMIT

    if voucher.usage_limit is not None and with_lock:
        code = Select * from voucher_codes where code=checkout_info.voucher_code FOR UPDATE

    ** _increase_checkout_voucher_usage part
    if checkout.is_voucher_usage_increased: TRANSACTION COMMIT
    if voucher.usage_limit: # increase_voucher_code_usage_value
        from voucher_codes set usage=usage+1 where code=checkout_info.voucher_code
    if voucher.apply_once_per_customer and increase_voucher_customer_usage: # add_voucher_usage_by_customer
        if not customer_email: TRANSACTION ABORT
        created = get_or_create from voucher_customer where voucher_id=code and customer_email=customer_email
        if not created: TRANSACTION ABORT
    if voucher.single_use: # deactivate_voucher_code
        from voucher_codes set is_active=False where code=checkout_info.voucher_code

    TRANSACTION COMMIT
    """
    t = Transaction()
    with_lock = True
    
    if voucher_code is not None:
        # Get code using voucher_code
        code = Code()
        t.append_read(f"voucher_id({code.voucher_id})")
        if code.voucher_id == 0: # if the code DNE
            return t

        # Get voucher using code.voucher_id
        voucher = Voucher()

        if voucher.is_voucher_usage_increased:
            voucher_invalid = np.random.binomial(1, 0.5) # Chance of voucher being invalid after fully being used (deactivated)
            if voucher_invalid:
                t.append_read(f"vouncher_code({voucher_code})")
                return t
        t.append_read(f"vouncher_code({voucher_code})")
        
        if voucher.usage_limit > 0 and with_lock:
            t.append_read(f"voucher_id({code.voucher_id})")
        
    # Increase voucher usage
    if voucher.usage_limit:
        t.append_write(f"usage_limit({code.used + 1})")
    if voucher.apply_once_per_customer:
        t.append_write(f"apply_once({voucher_code})")
    if voucher.single_use:
        t.append_write(f"single_use({False})")
    return t

def saleor_checkout_voucher_code_sim():
    """
    Example output:

    ['r-voucher_id(39)', 'r-vouncher_code(92)', 'r-voucher_id(39)', 'w-usage_limit(5)', 'w-apply_once(92)']
    ['r-voucher_id(93)', 'r-vouncher_code(7)', 'r-voucher_id(93)', 'w-usage_limit(4)', 'w-apply_once(7)']
    ['r-voucher_id(70)', 'r-vouncher_code(12)', 'r-voucher_id(70)', 'w-usage_limit(4)', 'w-single_use(False)']
    ['r-voucher_id(65)', 'r-vouncher_code(64)', 'r-voucher_id(65)', 'w-usage_limit(8)']
    ['r-voucher_id(62)', 'r-vouncher_code(1)']
    ['r-voucher_id(80)', 'r-vouncher_code(47)', 'r-voucher_id(80)', 'w-usage_limit(4)']
    ['r-voucher_id(92)', 'r-vouncher_code(88)', 'r-voucher_id(92)', 'w-usage_limit(9)', 'w-apply_once(88)']
    ['r-voucher_id(27)', 'r-vouncher_code(80)']
    ['r-voucher_id(55)', 'r-vouncher_code(48)']
    """
    voucher_codes = list(range(100))
    num_t = 10
    for _ in range(num_t):
        voucher_code = np.random.choice(voucher_codes)
        result = saleor_checkout_voucher_code_generator(voucher_code)
        print(result)

### Transaction 2 (Transaction 5, 6, 16 from Tang et al.) ###
def saleor_checkout_payment_process_generator(checkout_pk: int) -> list[str]:
    """
    Purpose: Coordinate concurrent checkout.
    saleor/checkout/complete_checkout.py#complete_checkout(with payment to process)
    
    Focusing on payment portion of complete_checkout_with_payment
    This includes _process_payment and _complete_checkout_fail_handler
    https://github.com/saleor/saleor/blob/c0423c3cd4968b287d71896d086e03483ac196d1/saleor/checkout/complete_checkout.py#L1754
    PSEUDOCODE:
    In: checkout_pk, payment 
    TRANSACTION START
    checkout = Select * from Checkout where pk=checkout_pk FOR UPDATE LIMIT 1
    if not checkout: 
        order = Select * from Order where checkout_id=checkout_pk
        TRANSACTION COMMIT

    payment = Select * from Payment where id=payment_id FOR UPDATE
    
    ** _process_payment part (note this is not exactly how the code is laid out but logically is the same
    ie. there's some redundant code across helper fns that I consolidated)
    try:
        if payment.to_confirm: (default is False)
            t = Select * from Transactions where kind=ACTION_TO_CONFIRM LIMIT 1 (get_action_to_confirm)
        response, error = _fetch_gateway_response
        if response: 
            update_payment (save) –> write
        if gateway_response.transaction_already_processed:
            t = Select * from Transactions where ... DESCENDING LIMIT 1 (get_already_processed_transaction)
        else: 
            t = "create_transaction" (not r/w)
    except error:
        _complete_checkout_fail_handler
    
    ** _complete_checkout_fail_handler part
    refresh_from_db(payment)
    if not payment_is_active:
        if checkout.completing_started_at is not None:
            append to update_fields
        
        if voucher: 
            if checkout_update_fields is None:
                is_voucher_usage_increased=False (save) –> write
            if voucher_code:
                if voucher.usage_limit: # decrease_voucher_code_usage_value
                    from voucher_codes set usage=usage-1 where code=checkout_info.voucher_code
                if voucher.single_use: # deactivate_voucher_code
                    from voucher_codes set is_active=False where code=checkout_info.voucher_code
                if user_email:
                    voucher_customer = Select * from voucher_customer where voucher_id=code and customer_email=user_email
                    if voucher_customer: delete –> write
        if update_fields:
            checkout (save) –> write
        
        if payment: # called with transaction_id = None
            if payment.can_refund():
                t = select * from transactions where kind=kind DESC LIMIT 1
                if t is None: TRANSACTION ABORT
                select * from transactions where payment_id=payment_id and kind=kind
                TRANSACTION COMMIT
            elif payment.can_void():
                t = select * from transactions where kind=kind DESC LIMIT 1
                if t is None: TRANSACTION ABORT
                select * from transactions where payment_id=payment_id and kind=kind
                TRANSACTION COMMIT
                
    TRANSACTION COMMIT
    """
    t = Transaction()

    checkout = Checkout()
    t.append_read(f"checkout_pk({checkout_pk})")
    if not checkout.exists:
        t.append_read(f"checkout_pk({checkout_pk})")
        return t
    
    payment = Payment()
    t.append_read(f"payment_id({payment.id})")
    try:
        if payment.to_confirm:
            t.append_read(f"ACTION_TO_CONFIRM")
        response = np.random.binomial(1, 0.5)
        if response:
            t.append_write(f"payment_id({payment.id})")
        gateway_response = np.random.binomial(1, 0.5)
        if gateway_response:
            t.append_read(f"TRANSACTION")
    except:
        t = complete_checkout_fail_handler(checkout, payment, t)

    if not payment.is_active:
        t = complete_checkout_fail_handler(checkout, payment, t)
    return t

def complete_checkout_fail_handler(checkout: Checkout, payment: Payment, t: Transaction) -> list[str]:
    update_fields = []
    if checkout.completing_started_at is not None:
        update_fields.append("completing_started_at")
    
    voucher = Voucher()
    if voucher.exists:
        if not checkout.is_voucher_usage_increased:
            pass
        else:
            if not update_fields:
                t.append_write(f"is_voucher_usage_increased")
            else:
                update_fields.append("is_voucher_usage_increased")
            if voucher.usage_limit:
                t.append_write(f"w-{voucher.usage_limit - 1}")
            if voucher.single_use:
                t.append_write(f"w-{False}")
            if voucher.apply_once_per_customer:
                t.append_write(f"w-{voucher.apply_once_per_customer}")
    if update_fields:
        t.append_write(f"checkout")
    
    if payment:
        if payment.can_refund:
            t.append_read(f"refund")
            if t is None:
                return t
            t.append_read(f"refund")
        elif payment.can_void:
            t.append_read(f"void")
            if t is None:
                return t
            t.append_read(f"void")   
    return t

def saleor_checkout_payment_process_sim():
    """
    Example output:

    ['r-checkout_pk(3)', 'r-payment_id(72)', 'r-ACTION_TO_CONFIRM', 'w-payment_id(72)', 'r-TRANSACTION']
    ['r-checkout_pk(77)', 'r-payment_id(41)', 'w-payment_id(41)']
    ['r-checkout_pk(96)', 'r-payment_id(92)', 'w-payment_id(92)', 'r-TRANSACTION']
    ['r-checkout_pk(56)', 'r-payment_id(45)', 'r-ACTION_TO_CONFIRM', 'r-TRANSACTION', 'w-checkout']
    ['r-checkout_pk(58)', 'r-payment_id(70)', 'r-refund', 'r-refund']
    ['r-checkout_pk(47)', 'r-checkout_pk(47)']
    ['r-checkout_pk(37)', 'r-payment_id(91)', 'r-TRANSACTION']
    ['r-checkout_pk(15)', 'r-payment_id(99)', 'r-ACTION_TO_CONFIRM', 'w-payment_id(99)']
    ['r-checkout_pk(5)', 'r-payment_id(44)', 'r-ACTION_TO_CONFIRM', 'r-TRANSACTION']
    ['r-checkout_pk(44)', 'r-payment_id(83)', 'r-TRANSACTION']
    """
    checkout_pks = list(range(100))
    num_t = 10
    for _ in range(num_t):
        checkout_pk = np.random.choice(checkout_pks)
        result = saleor_checkout_payment_process_generator(checkout_pk)
        print(result)

### Transaction 3 (Transaction 7 from Tang et al.) ###
def saleor_cancel_order_generator(fulfillment_pk: int) -> list[str]:
    """
    Purpose: Coordinate concurrent order cancellation.
    saleor/order/actions.py#cancel_fulfillment
    
    https://github.com/saleor/saleor/blob/c0423c3cd4968b287d71896d086e03483ac196d1/saleor/order/actions.py#L776
    PSEUDOCODE: 
    In: fulfillment_pk
    TRANSACTION START
    fulfillment = Select * from Fulfillment where pk=fulfillment.pk FOR UPDATE
    if warehouse:
        for line in fulfillment:
            if line.order_line.variant and line.order_line.variant.track_inventory:
                stock = Select * from Stock where pk=line.order_line.variant.pk FOR UPDATE LIMIT 1  
        bulk_update (write)
    fulfillment_status (save) –> write
    TRANSACTION COMMIT
    """
    t = Transaction()

    fulfillment = Fulfillment()
    t.append_read(f"fulfillment_pk({fulfillment_pk})")
    if fulfillment.warehouse:
        for line in fulfillment.lines:
            if line.order_line.variant and line.order_line.track_inventory:
                t.append_read(f"order_line_pk({line.order_line.pk})")
        t.append_write(f"fulfillment_pk({fulfillment_pk})")
    t.append_write(f"lines({len(fulfillment.lines)})")

    return t

def saleor_cancel_order_sim():
    """
    Example output:

    ['r-fulfillment_pk(13)', 'r-order_line_pk(79)', 'w-fulfillment_pk(13)', 'w-lines(1)']
    ['r-fulfillment_pk(13)', 'r-order_line_pk(88)', 'w-fulfillment_pk(13)', 'w-lines(7)']
    ['r-fulfillment_pk(63)', 'r-order_line_pk(37)', 'r-order_line_pk(74)', 'w-fulfillment_pk(63)', 'w-lines(7)']
    ['r-fulfillment_pk(93)', 'r-order_line_pk(1)', 'w-fulfillment_pk(93)', 'w-lines(7)']
    ['r-fulfillment_pk(48)', 'r-order_line_pk(30)', 'r-order_line_pk(5)', 'r-order_line_pk(12)', 'w-fulfillment_pk(48)', 'w-lines(4)']
    ['r-fulfillment_pk(54)', 'w-fulfillment_pk(54)', 'w-lines(1)']
    ['r-fulfillment_pk(76)', 'w-fulfillment_pk(76)', 'w-lines(1)']
    ['r-fulfillment_pk(70)', 'r-order_line_pk(68)', 'w-fulfillment_pk(70)', 'w-lines(3)']
    ['r-fulfillment_pk(57)', 'r-order_line_pk(48)', 'r-order_line_pk(76)', 'w-fulfillment_pk(57)', 'w-lines(3)']
    ['r-fulfillment_pk(98)', 'r-order_line_pk(86)', 'r-order_line_pk(27)', 'w-fulfillment_pk(98)', 'w-lines(5)']
    """
    fulfillment_pks = list(range(100))
    num_t = 10
    for _ in range(num_t):
        fulfillment_pk = np.random.choice(fulfillment_pks)
        result = saleor_cancel_order_generator(fulfillment_pk)
        print(result)

### Transaction 4 (Transaction 3 from Tang et al.) ###
def saleor_payment_order(order_pk: int, amount: float) -> list[str]:
    """
    Transaction 3
    Purpose: Coordinate concurrent payment processing.
    saleor/graphql/order/mutations/orders.py#OrderCapture

    https://github.com/saleor/saleor/blob/c738dcc49f65750fa39e6cd5c619f89e50184894/saleor/graphql/order/mutations/order_capture.py#L56
    PSEUDOCODE:
    In: order_id, amount
    TRANSACTION START
        order = SELECT * FROM Order WHERE id = order_id FOR UPDATE
        payment = SELECT * FROM Payment WHERE id = order.payment_id FOR UPDATE
        IF NOT payment.is_active:
            TRANSACTION ABORT
        IF amount <= 0:
            TRANSACTION ABORT
        transaction = CALL gateway.capture(payment, amount)
        WRITE transaction record -> write transaction details
        IF transaction.kind == TransactionKind.CAPTURE:
            site = SELECT * FROM Site FOR UPDATE
            UPDATE order status to "charged" -> write order record
            UPDATE payment status -> write payment record
    TRANSACTION COMMIT
    """
    t = Transaction()

    # Read order row from DB and lock it for update
    order = Order(order_pk)
    t.append_read(f"order_pk({order_pk})")
    
    # Read payment row (associated with the order) and lock it for update
    payment = order.payment
    t.append_read(f"payment_pk({payment.pk})")
    
    # Validation: payment must be active and amount must be positive.
    if not payment.is_active:
        return t # Abort transaction
    if amount <= 0:
        return t # Abort transaction
    
    # Perform the capture transaction via the payment gateway.
    # This call would normally create and record a new transaction.
    transaction = SaleorTransaction()  # Result from gateway.capture(payment, amount)
    t.append_write(f"transaction_pk({transaction.pk})")  # Write operation: saving the transaction record
    
    # If the capture transaction succeeded, update order and payment statuses.
    if transaction.kind == "CAPTURE":
        # Read site settings row for update (e.g., for logging or additional validation)
        site = Site()
        t.append_read(f"site_pk({site.pk})")
        
        # Write operations: updating order and payment statuses.
        t.append_write(f"order_pk({order.pk})")    # Write operation: update order status to 'charged'
        t.append_write(f"payment_pk{payment.pk})")  # Write operation: update payment status (captured)

    return t

def saleor_payment_order_sim():
    """
    Example output:

    ['r-order_pk(26)', 'r-payment_pk(31)', 'w-transaction_pk(86)']
    ['r-order_pk(2)', 'r-payment_pk(73)', 'w-transaction_pk(56)', 'r-site_pk(15)', 'w-order_pk(2)', 'w-payment_pk73)']
    ['r-order_pk(24)', 'r-payment_pk(9)', 'w-transaction_pk(76)', 'r-site_pk(40)', 'w-order_pk(24)', 'w-payment_pk9)']
    ['r-order_pk(6)', 'r-payment_pk(64)', 'w-transaction_pk(79)']
    ['r-order_pk(81)', 'r-payment_pk(66)', 'w-transaction_pk(30)', 'r-site_pk(35)', 'w-order_pk(81)', 'w-payment_pk66)']
    ['r-order_pk(67)', 'r-payment_pk(93)', 'w-transaction_pk(84)']
    ['r-order_pk(36)', 'r-payment_pk(22)']
    ['r-order_pk(19)', 'r-payment_pk(97)', 'w-transaction_pk(30)']
    ['r-order_pk(50)', 'r-payment_pk(66)']
    ['r-order_pk(1)', 'r-payment_pk(25)']
    """
    order_pks: int = list(range(100))
    amount: float = np.random.uniform(-10, 100)
    num_t = 10
    for _ in range(num_t):
        order_pk = np.random.choice(order_pks)
        result = saleor_payment_order(order_pk, amount)
        print(result)

### Transaction 5 (Transaction 8 from Tang et al.) ###
def saleor_order_fulfill_generator(order_id: str, input_data: dict) -> list[str]:
    """
    Transaction 8
    Purpose: Coordinate concurrent order fulfillment.
    saleor/graphql/order/mutations/fulfillments.py#OrderFulfill

    https://github.com/saleor/saleor/blob/c738dcc49f65750fa39e6cd5c619f89e50184894/saleor/graphql/order/mutations/order_fulfill.py#L252
    PSEUDOCODE:
    In: order_id, input_data
    TRANSACTION START
        order = SELECT * FROM Order WHERE id = order_id FOR UPDATE
        order_lines = SELECT * FROM OrderLine WHERE id IN (list of order_line_ids) FOR UPDATE
        for each order_line in order_lines:
            # Decide if this order_line will be fulfilled (e.g. random choice)
            IF eligible for fulfillment:
                # Get or create fulfillment record (locks or creates the row)
                fulfillment = SELECT * FROM Fulfillment WHERE order = order FOR UPDATE
                IF not exists:
                    fulfillment = INSERT INTO Fulfillment(order) VALUES (...)

                quantity = random.randrange(0, line.quantity) + 1
                # For the order line, read the allocation and associated stock records
                allocation = SELECT * FROM Allocation WHERE order_line = order_line FOR UPDATE
                stock = SELECT * FROM Stock WHERE id = allocation.stock_id FOR UPDATE

                quantity = calculated quantity # Determine fulfillment quantity (e.g., random quantity)
                INSERT INTO FulfillmentLine(fulfillment, order_line, quantity, stock) # New fulfillment line record
                UPDATE OrderLine SET quantity_fulfilled = quantity WHERE id = order_line.id
                UPDATE Allocation SET quantity_allocated = quantity_allocated - quantity WHERE id = allocation.pk
                UPDATE Stock SET quantity_allocated = quantity_allocated - quantity WHERE id = stock.pk

      t.append("w-{order_id}")  # update order record with new status
    TRANSACTION COMMIT
    """
    t = Transaction()
    
    # Read order record and lock for update
    t.append_read(f"order_id({order_id})")
    
    # Retrieve order lines (simulated from input_data)
    order_line_ids = input_data.get("order_line_ids", [])
    for line_id in order_line_ids:
        t.append_read(f"line_id({line_id})")
    
    # TODO: differentiate between different order lines in t list
    # Process each order line
    for line in input_data.get("lines", []):
        warehouse_id = line.get("warehouse")
        t.append_read(f"warehouse_id({warehouse_id})")
        
        # Simulate fulfillment decision and subsequent writes
        if line.get("fulfill", True):
            t.append_read("r-fulfillment")  # get_or_create fulfillment
            if not np.random.binomial(1, 0.5):  # If fulfillment doesn't exist
                t.append_write("fulfillment")
            t.append_read("alloc")
            t.append_read("stock")
            t.append_write("fulfillment_line")
            t.append_write("order_line")
            t.append_write("alloc")
            t.append_write("stock")   
    t.append_write(f"order_id({order_id})") # Update order status
    
    return t

def saleor_order_fulfill_sim():
    """
    Example output:

    ['r-order_id(78)', 'r-line_id(66)', 'r-line_id(95)', 'r-line_id(46)', 'r-warehouse_id(24)', 'r-r-fulfillment', 'r-alloc', 'r-stock', 'w-fulfillment_line', 'w-order_line', 'w-alloc', 'w-stock', 'r-warehouse_id(48)', 'r-warehouse_id(33)', 'w-order_id(78)']
    ['r-order_id(44)', 'r-line_id(71)', 'r-line_id(18)', 'r-warehouse_id(79)', 'r-r-fulfillment', 'w-fulfillment', 'r-alloc', 'r-stock', 'w-fulfillment_line', 'w-order_line', 'w-alloc', 'w-stock', 'r-warehouse_id(23)', 'w-order_id(44)']
    ['r-order_id(36)', 'r-line_id(47)', 'r-warehouse_id(43)', 'w-order_id(36)']
    ['r-order_id(28)', 'r-line_id(62)', 'r-line_id(17)', 'r-line_id(22)', 'r-warehouse_id(64)', 'r-r-fulfillment', 'w-fulfillment', 'r-alloc', 'r-stock', 'w-fulfillment_line', 'w-order_line', 'w-alloc', 'w-stock', 'r-warehouse_id(78)', 'r-r-fulfillment', 'w-fulfillment', 'r-alloc', 'r-stock', 'w-fulfillment_line', 'w-order_line', 'w-alloc', 'w-stock', 'r-warehouse_id(70)', 'r-r-fulfillment', 'w-fulfillment', 'r-alloc', 'r-stock', 'w-fulfillment_line', 'w-order_line', 'w-alloc', 'w-stock', 'w-order_id(28)']
    ['r-order_id(81)', 'r-line_id(65)', 'r-warehouse_id(33)', 'w-order_id(81)']
    ['r-order_id(53)', 'r-line_id(91)', 'r-line_id(16)', 'r-line_id(36)', 'r-line_id(99)', 'r-warehouse_id(13)', 'r-r-fulfillment', 'w-fulfillment', 'r-alloc', 'r-stock', 'w-fulfillment_line', 'w-order_line', 'w-alloc', 'w-stock', 'r-warehouse_id(43)', 'r-warehouse_id(22)', 'r-warehouse_id(12)', 'w-order_id(53)']
    ['r-order_id(21)', 'r-line_id(80)', 'r-line_id(2)', 'r-line_id(13)', 'r-line_id(26)', 'r-warehouse_id(23)', 'r-warehouse_id(94)', 'r-warehouse_id(50)', 'r-r-fulfillment', 'r-alloc', 'r-stock', 'w-fulfillment_line', 'w-order_line', 'w-alloc', 'w-stock', 'r-warehouse_id(41)', 'r-r-fulfillment', 'r-alloc', 'r-stock', 'w-fulfillment_line', 'w-order_line', 'w-alloc', 'w-stock', 'w-order_id(21)']
    ['r-order_id(56)', 'r-line_id(77)', 'r-warehouse_id(62)', 'r-r-fulfillment', 'w-fulfillment', 'r-alloc', 'r-stock', 'w-fulfillment_line', 'w-order_line', 'w-alloc', 'w-stock', 'w-order_id(56)']
    ['r-order_id(17)', 'r-line_id(20)', 'r-line_id(46)', 'r-warehouse_id(38)', 'r-warehouse_id(18)', 'w-order_id(17)']
    ['r-order_id(88)', 'r-line_id(30)', 'r-line_id(95)', 'r-line_id(36)', 'r-line_id(4)', 'r-warehouse_id(27)', 'r-warehouse_id(32)', 'r-warehouse_id(64)', 'r-r-fulfillment', 'w-fulfillment', 'r-alloc', 'r-stock', 'w-fulfillment_line', 'w-order_line', 'w-alloc', 'w-stock', 'r-warehouse_id(35)', 'r-r-fulfillment', 'r-alloc', 'r-stock', 'w-fulfillment_line', 'w-order_line', 'w-alloc', 'w-stock', 'w-order_id(88)']
    """
    order_ids = list(range(100))
    num_t = 10
    for _ in range(num_t):
        num_lines = np.random.choice(range(1, 5))
        input_data = {
            "order_line_ids": [np.random.choice(order_ids) for _ in range(num_lines)],
            # NOTE: "fulfill" being random choice between True/False IS in the original code
            "lines": [{"warehouse": np.random.choice(order_ids), "fulfill": np.random.binomial(1, 0.5)} for _ in range(num_lines)]
        }
        order_id = np.random.choice(order_ids)
        result = saleor_order_fulfill_generator(order_id, input_data)
        print(result)

### Transaction 6 (Transaction 15 from Tang et al.) ###
def saleor_order_lines_create_generator(order_id: str, input_data: dict) -> list[str]:
    """
    Transaction 15
    Purpose: Coordinate concurrent order updating.
    saleor/graphql/order/mutations/orders.py#OrderLineCreate

    https://github.com/saleor/saleor/blob/c738dcc49f65750fa39e6cd5c619f89e50184894/saleor/graphql/order/mutations/order_lines_create.py#L175
    PSEUDOCODE:
    In: order_id, input_data (which contains a list of new order line inputs)
    TRANSACTION START
        order = SELECT * FROM Order WHERE id = order_id FOR UPDATE
        For each line in input_data["lines"]:
            Read the product variant record
            Insert a new order line record -> write new_order_line
        Create products_added event –> write
        Invalidate order prices (update order.should_refresh_prices)
        Recalculate order weight:
            For each order line:
                Read order_line record
            Then update order weight –> write
        Update order search vector –> write
        Save the order record with update_fields –> write
        Trigger order status event –> write order_event_status
    TRANSACTION COMMIT
    """
    t = Transaction()

    # Read order record (lock for update)
    t.append_read(f"order_id({order_id})")

    # Process each new order line from input_data
    for line in input_data.get("lines", []):
        variant_id = line.get("variant_id")
        # Read product variant record (lock for update)
        t.append_read(f"variant_id({variant_id})")
        # Simulate writing a new order line record. Here we simulate an order line ID.
        order_line_id = f"line_{variant_id}"
        t.append_write(f"order_line_id({order_line_id})")

    # Create order event for added products
    t.append_write("order_event")
    # Invalidate order prices
    t.append_write(f"order_id({order_id})") # Update should_refresh_prices field

    # Recalculate order weight
    for line in input_data.get("lines", []):
        order_line_id = f"line_{line.get('variant_id')}"
        t.append_read(f"order_line_id({order_line_id})") # Read each order line for weight calculation
    t.append_write(f"order_weight({order_id})") # Update order weight field

    t.append_write(f"search_vector({order_id})") # Update search_vector field
    t.append_write(f"order_id({order_id})") # Save the order (final write)
    t.append_write("order_event_status")     # Call event by order status (simulate writing order event status update)

    return t

def saleor_order_lines_create_sim():
    """
    Example output:

    ['r-order_id(58)', 'r-variant_id(77)', 'w-order_line_id(line_77)', 'r-variant_id(83)', 'w-order_line_id(line_83)', 'r-variant_id(90)', 'w-order_line_id(line_90)', 'r-variant_id(10)', 'w-order_line_id(line_10)', 'r-variant_id(57)', 'w-order_line_id(line_57)', 'r-variant_id(36)', 'w-order_line_id(line_36)', 'r-variant_id(50)', 'w-order_line_id(line_50)', 'r-variant_id(77)', 'w-order_line_id(line_77)', 'r-variant_id(72)', 'w-order_line_id(line_72)', 'w-order_event', 'w-order_id(58)', 'r-order_line_id(line_77)', 'r-order_line_id(line_83)', 'r-order_line_id(line_90)', 'r-order_line_id(line_10)', 'r-order_line_id(line_57)', 'r-order_line_id(line_36)', 'r-order_line_id(line_50)', 'r-order_line_id(line_77)', 'r-order_line_id(line_72)', 'w-order_weight(58)', 'w-search_vector(58)', 'w-order_id(58)', 'w-order_event_status']
    ['r-order_id(33)', 'r-variant_id(26)', 'w-order_line_id(line_26)', 'r-variant_id(17)', 'w-order_line_id(line_17)', 'w-order_event', 'w-order_id(33)', 'r-order_line_id(line_26)', 'r-order_line_id(line_17)', 'w-order_weight(33)', 'w-search_vector(33)', 'w-order_id(33)', 'w-order_event_status']
    ['r-order_id(84)', 'r-variant_id(37)', 'w-order_line_id(line_37)', 'r-variant_id(30)', 'w-order_line_id(line_30)', 'r-variant_id(39)', 'w-order_line_id(line_39)', 'r-variant_id(84)', 'w-order_line_id(line_84)', 'r-variant_id(44)', 'w-order_line_id(line_44)', 'w-order_event', 'w-order_id(84)', 'r-order_line_id(line_37)', 'r-order_line_id(line_30)', 'r-order_line_id(line_39)', 'r-order_line_id(line_84)', 'r-order_line_id(line_44)', 'w-order_weight(84)', 'w-search_vector(84)', 'w-order_id(84)', 'w-order_event_status']
    ['r-order_id(49)', 'r-variant_id(60)', 'w-order_line_id(line_60)', 'r-variant_id(43)', 'w-order_line_id(line_43)', 'r-variant_id(25)', 'w-order_line_id(line_25)', 'r-variant_id(26)', 'w-order_line_id(line_26)', 'r-variant_id(79)', 'w-order_line_id(line_79)', 'r-variant_id(26)', 'w-order_line_id(line_26)', 'r-variant_id(76)', 'w-order_line_id(line_76)', 'w-order_event', 'w-order_id(49)', 'r-order_line_id(line_60)', 'r-order_line_id(line_43)', 'r-order_line_id(line_25)', 'r-order_line_id(line_26)', 'r-order_line_id(line_79)', 'r-order_line_id(line_26)', 'r-order_line_id(line_76)', 'w-order_weight(49)', 'w-search_vector(49)', 'w-order_id(49)', 'w-order_event_status']
    ['r-order_id(55)', 'r-variant_id(74)', 'w-order_line_id(line_74)', 'r-variant_id(38)', 'w-order_line_id(line_38)', 'r-variant_id(81)', 'w-order_line_id(line_81)', 'w-order_event', 'w-order_id(55)', 'r-order_line_id(line_74)', 'r-order_line_id(line_38)', 'r-order_line_id(line_81)', 'w-order_weight(55)', 'w-search_vector(55)', 'w-order_id(55)', 'w-order_event_status']
    ['r-order_id(86)', 'r-variant_id(90)', 'w-order_line_id(line_90)', 'r-variant_id(87)', 'w-order_line_id(line_87)', 'r-variant_id(85)', 'w-order_line_id(line_85)', 'w-order_event', 'w-order_id(86)', 'r-order_line_id(line_90)', 'r-order_line_id(line_87)', 'r-order_line_id(line_85)', 'w-order_weight(86)', 'w-search_vector(86)', 'w-order_id(86)', 'w-order_event_status']
    ['r-order_id(85)', 'r-variant_id(81)', 'w-order_line_id(line_81)', 'r-variant_id(66)', 'w-order_line_id(line_66)', 'r-variant_id(9)', 'w-order_line_id(line_9)', 'r-variant_id(7)', 'w-order_line_id(line_7)', 'r-variant_id(98)', 'w-order_line_id(line_98)', 'r-variant_id(59)', 'w-order_line_id(line_59)', 'r-variant_id(19)', 'w-order_line_id(line_19)', 'r-variant_id(61)', 'w-order_line_id(line_61)', 'r-variant_id(62)', 'w-order_line_id(line_62)', 'w-order_event', 'w-order_id(85)', 'r-order_line_id(line_81)', 'r-order_line_id(line_66)', 'r-order_line_id(line_9)', 'r-order_line_id(line_7)', 'r-order_line_id(line_98)', 'r-order_line_id(line_59)', 'r-order_line_id(line_19)', 'r-order_line_id(line_61)', 'r-order_line_id(line_62)', 'w-order_weight(85)', 'w-search_vector(85)', 'w-order_id(85)', 'w-order_event_status']
    ['r-order_id(77)', 'r-variant_id(76)', 'w-order_line_id(line_76)', 'r-variant_id(41)', 'w-order_line_id(line_41)', 'r-variant_id(58)', 'w-order_line_id(line_58)', 'r-variant_id(87)', 'w-order_line_id(line_87)', 'r-variant_id(6)', 'w-order_line_id(line_6)', 'r-variant_id(37)', 'w-order_line_id(line_37)', 'w-order_event', 'w-order_id(77)', 'r-order_line_id(line_76)', 'r-order_line_id(line_41)', 'r-order_line_id(line_58)', 'r-order_line_id(line_87)', 'r-order_line_id(line_6)', 'r-order_line_id(line_37)', 'w-order_weight(77)', 'w-search_vector(77)', 'w-order_id(77)', 'w-order_event_status']
    ['r-order_id(23)', 'r-variant_id(63)', 'w-order_line_id(line_63)', 'r-variant_id(68)', 'w-order_line_id(line_68)', 'r-variant_id(80)', 'w-order_line_id(line_80)', 'r-variant_id(94)', 'w-order_line_id(line_94)', 'w-order_event', 'w-order_id(23)', 'r-order_line_id(line_63)', 'r-order_line_id(line_68)', 'r-order_line_id(line_80)', 'r-order_line_id(line_94)', 'w-order_weight(23)', 'w-search_vector(23)', 'w-order_id(23)', 'w-order_event_status']
    ['r-order_id(48)', 'r-variant_id(98)', 'w-order_line_id(line_98)', 'r-variant_id(1)', 'w-order_line_id(line_1)', 'r-variant_id(92)', 'w-order_line_id(line_92)', 'r-variant_id(8)', 'w-order_line_id(line_8)', 'r-variant_id(40)', 'w-order_line_id(line_40)', 'r-variant_id(5)', 'w-order_line_id(line_5)', 'w-order_event', 'w-order_id(48)', 'r-order_line_id(line_98)', 'r-order_line_id(line_1)', 'r-order_line_id(line_92)', 'r-order_line_id(line_8)', 'r-order_line_id(line_40)', 'r-order_line_id(line_5)', 'w-order_weight(48)', 'w-search_vector(48)', 'w-order_id(48)', 'w-order_event_status']
    """
    order_ids = list(range(100))
    num_t = 10
    for _ in range(num_t):
        num_lines = np.random.choice(range(1, 10))
        input_data = {
            "lines": [{"variant_id": np.random.choice(order_ids)} for _ in range(num_lines)]
        }
        order_id = np.random.choice(order_ids)
        result = saleor_order_lines_create_generator(order_id, input_data)
        print(result)

### Transaction 7 (Transaction 11, 12 from Tang et al.) ###
def saleor_stripe_handle_authorized_payment_intent_generator(payment_intent: StripePaymentObj) -> list[str]:
    """
    Purpose: Coordinate concurrent payment processing.
    saleor/payment/gateways/stripe/webhooks.py#handle_authorized_payment_intent

    https://github.com/saleor/saleor/blob/c738dcc49f65750fa39e6cd5c619f89e50184894/saleor/payment/gateways/stripe/webhooks.py#L302C5-L302C37
    PSEUDOCODE:
    TRANSACTION START
        payment = SELECT * FROM Payment WHERE transactions.token = '{payment_intent_id}'
        if checkout_exists:
            checkout = SELECT * FROM Checkout WHERE payment_id = payment_id AND is_active = TRUE FOR UPDATE
        # Re-read Payment with a lock (to avoid race conditions)
        payment = SELECT * FROM Payment WHERE transactions.token = '{payment_intent_id}' FOR UPDATE
        UPDATE Payment SET payment_method_details = 'new_method_details' WHERE id = payment_id;
      
        If Payment is NOT active:
            SELECT * FROM Transaction WHERE payment_id = payment_id AND kind = 'AUTH'
            INSERT INTO Transaction (payment_id, kind, amount, currency) VALUES ...
            UPDATE Payment SET charge_status = 'VOIDED' WHERE id = payment_id
      
        Elif Payment is linked to an Order:
            If charge status is PENDING:
                INSERT INTO Transaction (payment_id, kind, amount, currency) VALUES ... 
        
        Elif Checkout exists (and no Order):
            SELECT * FROM Transaction WHERE payment_id = payment_id AND kind = 'AUTH'
            INSERT INTO Transaction (payment_id, kind, amount, currency) VALUES ...
            UPDATE Payment SET charge_status = 'UPDATED' WHERE id = payment_id
            SELECT * FROM Checkout WHERE id = checkout_id FOR UPDATE
            INSERT INTO Order (order_data) VALUES ('order_info')
    """
    t = Transaction()
    payment = Payment()
    checkout = Checkout()

    t.append_read(f"payment_intent_id({payment_intent.payment_intent_id})")
       
    if payment_intent.checkout_exists:
        t.append_read(f"payment_id({payment.id})")

    # Re-read Payment with lock
    t.append_read(f"payment_intent_id({payment_intent.payment_intent_id})")
    t.append_write(f"update_pmt_details({payment.id})")

    if not payment_intent.payment_active:
        # Payment is inactive –> void/refund branch.
        t.append_read(f"transaction({payment.id})")
        t.append_write(f"insert_into_transaction({payment.id})")
        t.append_write(f"update_payment({payment.id})")
    elif payment_intent.payment_order_exists:
        if payment_intent.payment_charge_status_pending:
            t.append_write(f"insert_into_transaction({payment.id})")
    elif payment_intent.checkout_exists:
        # Processing via checkout branch.
        t.append_read(f"payment_id({payment.id})")
        t.append_write(f"insert_into_transaction({payment.id})")
        t.append_write(f"update_payment({payment.id})")
        t.append_read(f"checkout_id({checkout.id})")
        t.append_write(f"insert_into_order({payment.order_id})")

    return t

def saleor_stripe_handle_authorized_payment_intent_sim():
    """
    Example output:

    ['r-payment_intent_id(30)', 'r-payment_id(99)', 'r-payment_intent_id(30)', 'w-update_pmt_details(99)', 'r-transaction(99)', 'w-insert_into_transaction(99)', 'w-update_payment(99)']
    ['r-payment_intent_id(58)', 'r-payment_intent_id(58)', 'w-update_pmt_details(70)']
    ['r-payment_intent_id(47)', 'r-payment_id(90)', 'r-payment_intent_id(47)', 'w-update_pmt_details(90)', 'r-transaction(90)', 'w-insert_into_transaction(90)', 'w-update_payment(90)']
    ['r-payment_intent_id(70)', 'r-payment_id(31)', 'r-payment_intent_id(70)', 'w-update_pmt_details(31)', 'w-insert_into_transaction(31)']
    ['r-payment_intent_id(65)', 'r-payment_intent_id(65)', 'w-update_pmt_details(97)', 'r-transaction(97)', 'w-insert_into_transaction(97)', 'w-update_payment(97)']
    ['r-payment_intent_id(45)', 'r-payment_id(74)', 'r-payment_intent_id(45)', 'w-update_pmt_details(74)', 'r-transaction(74)', 'w-insert_into_transaction(74)', 'w-update_payment(74)']
    ['r-payment_intent_id(22)', 'r-payment_intent_id(22)', 'w-update_pmt_details(85)', 'r-transaction(85)', 'w-insert_into_transaction(85)', 'w-update_payment(85)']
    ['r-payment_intent_id(0)', 'r-payment_id(85)', 'r-payment_intent_id(0)', 'w-update_pmt_details(85)', 'r-payment_id(85)', 'w-insert_into_transaction(85)', 'w-update_payment(85)', 'r-checkout_id(0)', 'w-insert_into_order(5)']
    ['r-payment_intent_id(23)', 'r-payment_intent_id(23)', 'w-update_pmt_details(13)', 'w-insert_into_transaction(13)']
    ['r-payment_intent_id(67)', 'r-payment_intent_id(67)', 'w-update_pmt_details(60)', 'r-transaction(60)', 'w-insert_into_transaction(60)', 'w-update_payment(60)']
    """
    num_t = 10
    for _ in range(num_t):
        payment_intent = StripePaymentObj()
        result = saleor_stripe_handle_authorized_payment_intent_generator(payment_intent)
        print(result)

### Transaction 8 (Transaction 14 from Tang et al.) ###
def saleor_stock_bulk_update_generator(stocks: list[dict], fields_to_update: list[str]) -> list[str]:
    """
    Transaction 14
    Purpose: Coordinate concurrent order updating.
    saleor/warehouse/management.py#StockBulkUpdate
    
    https://github.com/saleor/saleor/blob/716be111ef3cb9310824174de2416491a141d8f3/saleor/warehouse/management.py#L64
    PSEUDOCODE:
    In: 
    TRANSACTION START
      SELECT id FROM Stock WHERE id IN ([stock_ids]) FOR UPDATE
      BULK UPDATE Stock SET <fields_to_update> WHERE id IN ([stock_ids])
    TRANSACTION COMMIT
    """
    t = Transaction()

    stock_ids = [stock["id"] for stock in stocks]
    stock_ids_str = ", ".join([str(stock_id) for stock_id in stock_ids])
    t.append_read(f"stock_ids({stock_ids_str})")
    fields_to_update_str = ", ".join(fields_to_update)
    t.append_write(f"fields_to_update({fields_to_update_str})") # Bulk update the stocks with the given fields
    
    return t

def saleor_stock_bulk_update_sim():
    """
    Example output:

    ['r-stock_ids(61)', 'w-fields_to_update(quantity, price)']
    ['r-stock_ids(34, 13, 8)', 'w-fields_to_update(quantity, price)']
    ['r-stock_ids(15)', 'w-fields_to_update(quantity, price)']
    ['r-stock_ids(34, 30, 12, 40, 22)', 'w-fields_to_update(quantity, price)']
    ['r-stock_ids(30, 13, 68, 56)', 'w-fields_to_update(quantity, price)']
    ['r-stock_ids(65, 63, 0, 42, 38, 18, 25, 38)', 'w-fields_to_update(quantity, price)']
    ['r-stock_ids(99, 61, 71, 83, 61, 74, 2, 34, 56)', 'w-fields_to_update(quantity, price)']
    ['r-stock_ids(94, 23, 56, 67, 56, 65, 52, 77)', 'w-fields_to_update(quantity, price)']
    ['r-stock_ids(70, 4, 86, 55)', 'w-fields_to_update(quantity, price)']
    ['r-stock_ids(61)', 'w-fields_to_update(quantity, price)']
    """
    num_t = 10
    for _ in range(num_t):
        stocks = [
            {"id": np.random.choice(range(100)), "quantity": np.random.randint(1, 100), "price": np.random.uniform(10, 100)}
            for _ in range(np.random.randint(1, 10))
        ]
        fields_to_update = ["quantity", "price"]
        result = saleor_stock_bulk_update_generator(stocks, fields_to_update)
        print(result)

### Transaction 9 (Transaction 13 from Tang et al.) ###
def saleor_delete_categories_generator(categories_ids: list) -> list[str]:
    """
    Purpose: Coordinate concurrent categories updating.
    saleor/product/utils/__init__.py#delete_categories

    https://github.com/saleor/saleor/blob/1337f67b001927aac5c30854debdd1de8e6ccfcf/saleor/product/utils/__init__.py#L38C1-L67C76
    PSEUDOCODE:
    TRANSACTION START
        categories = SELECT * FROM Category WHERE id IN categories_ids FOR UPDATE
        products = SELECT * FROM Product WHERE category_id IN categories_ids

        product_channel_listing = SELECT * FROM ProductChannelListing WHERE product_id IN ([101, 102, 103]);
        UPDATE ProductChannelListing SET is_published = FALSE, published_at = NULL # Unpublish product listings for deleted categories
        
        DELETE FROM Category WHERE id IN categories_ids
        
        channel_ids = SELECT DISTINCT channel_id FROM ProductChannelListing WHERE product_id IN products
    TRANSACTION COMMIT
    """
    t = Transaction()
    
    t.append_read(f"categories({categories_ids})")

    all_product_ids = []
    
    for category_id in categories_ids:
        num_products = np.random.randint(1, 6)
        product_ids = np.random.randint(100, 1000, size=num_products).tolist()
        all_product_ids.append(product_ids)
    t.append_read(f"prefetch_products({all_product_ids})")
    
    t.append_read(f"product_channel_listing({product_ids})")
    
    t.append_write(f"product_channel_listing")
    
    t.append_write(f"delete_categories({categories_ids})")
    
    t.append_read(f"channel_id({product_ids})")
    
    return t

def saleor_delete_categories_sim():
    """
    Example output:

    ['r-categories([550, 79])', 'r-prefetch_products([[206, 847, 866, 679, 400], [486, 174, 186, 630, 462]])', 'r-product_channel_listing([486, 174, 186, 630, 462])', 'w-product_channel_listing', 'w-delete_categories([550, 79])', 'r-channel_id([486, 174, 186, 630, 462])']
    ['r-categories([843, 228])', 'r-prefetch_products([[457, 529, 905, 255, 946], [627, 374, 559]])', 'r-product_channel_listing([627, 374, 559])', 'w-product_channel_listing', 'w-delete_categories([843, 228])', 'r-channel_id([627, 374, 559])']
    ['r-categories([562, 32, 431, 157])', 'r-prefetch_products([[572], [347, 410, 738], [361, 420, 571, 289], [120, 424, 513]])', 'r-product_channel_listing([120, 424, 513])', 'w-product_channel_listing', 'w-delete_categories([562, 32, 431, 157])', 'r-channel_id([120, 424, 513])']
    ['r-categories([651, 64, 631])', 'r-prefetch_products([[780, 232], [396, 778, 904, 494], [852, 963, 520, 587]])', 'r-product_channel_listing([852, 963, 520, 587])', 'w-product_channel_listing', 'w-delete_categories([651, 64, 631])', 'r-channel_id([852, 963, 520, 587])']
    ['r-categories([282])', 'r-prefetch_products([[321, 429, 979, 616]])', 'r-product_channel_listing([321, 429, 979, 616])', 'w-product_channel_listing', 'w-delete_categories([282])', 'r-channel_id([321, 429, 979, 616])']
    ['r-categories([530, 892])', 'r-prefetch_products([[365], [238, 334, 334]])', 'r-product_channel_listing([238, 334, 334])', 'w-product_channel_listing', 'w-delete_categories([530, 892])', 'r-channel_id([238, 334, 334])']
    ['r-categories([660, 929])', 'r-prefetch_products([[707], [834]])', 'r-product_channel_listing([834])', 'w-product_channel_listing', 'w-delete_categories([660, 929])', 'r-channel_id([834])']
    ['r-categories([566, 145, 912])', 'r-prefetch_products([[315, 446], [897], [179, 855, 439, 948, 314]])', 'r-product_channel_listing([179, 855, 439, 948, 314])', 'w-product_channel_listing', 'w-delete_categories([566, 145, 912])', 'r-channel_id([179, 855, 439, 948, 314])']
    ['r-categories([185, 261])', 'r-prefetch_products([[596, 721, 502], [956, 927, 680]])', 'r-product_channel_listing([956, 927, 680])', 'w-product_channel_listing', 'w-delete_categories([185, 261])', 'r-channel_id([956, 927, 680])']
    ['r-categories([538, 705, 232, 403])', 'r-prefetch_products([[948, 645, 713, 761], [133, 137, 819, 955], [617, 486, 139], [534, 669, 264, 700]])', 'r-product_channel_listing([534, 669, 264, 700])', 'w-product_channel_listing', 'w-delete_categories([538, 705, 232, 403])', 'r-channel_id([534, 669, 264, 700])']
    """
    num_t = 10
    for _ in range(num_t):
        categories_ids = np.random.randint(1, 1000, size=np.random.randint(1, 5)).tolist()
        result = saleor_delete_categories_generator(categories_ids)
        print(result)

def main():
    saleor_checkout_voucher_code_sim() # Transaction 1
    # saleor_checkout_payment_process_sim() # Transaction 2
    # saleor_cancel_order_sim() # Transaction 3
    # saleor_payment_order_sim() # Transaction 4
    # saleor_order_fulfill_sim() # Transaction 5
    # saleor_order_lines_create_sim() # Transaction 6
    # saleor_stripe_handle_authorized_payment_intent_sim() # Transaction 7
    # saleor_stock_bulk_update_sim() # Transaction 8
    # saleor_delete_categories_sim() # Transaction 9

if __name__ == '__main__':
    main()