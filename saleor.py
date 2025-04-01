# https://github.com/saleor/saleor
# Uses PostgreSQL
# Found in Tang et al. Ad Hoc Transactions in Web Applications: The Good, the Bad, and the Ugly

# Contextual note: select_for_update is used to lock rows until the end of the transaction. 
# Django docs: https://docs.djangoproject.com/en/5.1/ref/models/querysets/#select-for-update 

import numpy as np
import datetime

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
        self.is_active: bool = np.random.binomial(1, 0.5)
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
        self.track_inventory = np.random.binomial(1, 0.5)
        self.pk = np.random.choice(range(100))

class Order:
    def __init__(self, order_pk: int):
        self.pk: int = order_pk
        self.payment: Payment = Payment()
        self.status: str = "pending"
        self.exists: bool = np.random.binomial(1, 0.5)

class Transaction: 
    def __init__(self):
        self.kind: str = np.random.choice(["ACTION_TO_CONFIRM", "CAPTURE", "REFUND", "VOID"])
        self.pk: int = np.random.choice(range(100))

class Site:
    def __init__(self):
        self.pk: int = np.random.choice(range(100))

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
    txn = []

    with_lock = True
    
    if voucher_code is not None:
        # Get code using voucher_code
        code = Code()
        txn.append(f"r-{code.voucher_id}")
        if code.voucher_id == 0: # if the code DNE
            return txn

        # Get voucher using code.voucher_id
        voucher = Voucher()

        if voucher.is_voucher_usage_increased:
            voucher_invalid = np.random.binomial(1, 0.5) # Chance of voucher being invalid after fully being used (deactivated)
            if voucher_invalid:
                txn.append(f"r-{voucher_code}")
                return txn
        txn.append(f"r-{voucher_code}")
        
        if voucher.usage_limit > 0 and with_lock:
            txn.append(f"r-{code.voucher_id}")
        
    # Increase voucher usage
    if voucher.usage_limit:
        txn.append(f"w-{code.used + 1}")
    if voucher.apply_once_per_customer:
        txn.append(f"w-{voucher_code}")
    if voucher.single_use:
        txn.append(f"w-{False}")
    return txn

def saleor_checkout_voucher_code_sim():
    """
    Example output:

    ['r-76', 'r-32', 'r-76', 'w-6', 'w-32', 'w-False']
    ['r-22', 'r-33']
    ['r-23', 'r-15', 'r-23', 'w-4']
    ['r-53', 'r-43']
    ['r-31', 'r-47', 'r-31', 'w-4']
    ['r-34', 'r-29']
    ['r-58', 'r-83', 'r-58', 'w-6', 'w-False']
    ['r-62', 'r-27', 'r-62', 'w-5', 'w-27']
    ['r-42', 'r-35', 'r-42', 'w-10', 'w-35']
    ['r-21', 'r-96', 'r-21', 'w-8']
    """
    voucher_codes = list(range(100))
    num_txn = 10
    for _ in range(num_txn):
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
            txn = Select * from Transactions where kind=ACTION_TO_CONFIRM LIMIT 1 (get_action_to_confirm)
        response, error = _fetch_gateway_response
        if response: 
            update_payment (save) –> write
        if gateway_response.transaction_already_processed:
            txn = Select * from Transactions where ... DESCENDING LIMIT 1 (get_already_processed_transaction)
        else: 
            txn = "create_transaction" (not r/w)
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
                txn = select * from transactions where kind=kind DESC LIMIT 1
                if txn is None: TRANSACTION ABORT
                select * from transactions where payment_id=payment_id and kind=kind
                TRANSACTION COMMIT
            elif payment.can_void():
                txn = select * from transactions where kind=kind DESC LIMIT 1
                if txn is None: TRANSACTION ABORT
                select * from transactions where payment_id=payment_id and kind=kind
                TRANSACTION COMMIT
                
    TRANSACTION COMMIT
    """
    txn = []

    checkout = Checkout()
    txn.append(f"r-{checkout_pk}")
    if not checkout.exists:
        txn.append(f"r-order{checkout_pk}")
        return txn
    
    payment = Payment()
    txn.append(f"r-{payment.id}")
    try:
        if payment.to_confirm:
            txn.append(f"r-ACTION_TO_CONFIRM")
        response = np.random.binomial(1, 0.5)
        if response:
            txn.append(f"w-{payment.id}")
        gateway_response = np.random.binomial(1, 0.5)
        if gateway_response:
            txn.append(f"r-TRANSACTION")
    except:
        txn = complete_checkout_fail_handler(checkout, payment, txn)

    if not payment.is_active:
        txn = complete_checkout_fail_handler(checkout, payment, txn)
    return txn

def complete_checkout_fail_handler(checkout: Checkout, payment: Payment, txn: list[str]) -> list[str]:
    update_fields = []
    if checkout.completing_started_at is not None:
        update_fields.append("completing_started_at")
    
    voucher = Voucher()
    if voucher.exists:
        if not checkout.is_voucher_usage_increased:
            pass
        else:
            if not update_fields:
                txn.append(f"w-is_voucher_usage_increased")
            else:
                update_fields.append("is_voucher_usage_increased")
            if voucher.usage_limit:
                txn.append(f"w-{voucher.usage_limit - 1}")
            if voucher.single_use:
                txn.append(f"w-{False}")
            if voucher.apply_once_per_customer:
                txn.append(f"w-{voucher.apply_once_per_customer}")
    if update_fields:
        txn.append(f"w-checkout")
    
    if payment:
        if payment.can_refund:
            txn.append(f"r-refund")
            if txn is None:
                return txn
            txn.append(f"r-refund")
        elif payment.can_void:
            txn.append(f"r-void")
            if txn is None:
                return txn
            txn.append(f"r-void")   
    return txn

def saleor_checkout_payment_process_sim():
    """
    Example output:

    ['r-13', 'r-80', 'r-ACTION_TO_CONFIRM']
    ['r-0', 'r-order0']
    ['r-16', 'r-19']
    ['r-30', 'r-31', 'w-31', 'r-TRANSACTION', 'r-void', 'r-void']
    ['r-54', 'r-95']
    ['r-35', 'r-71', 'r-TRANSACTION', 'r-refund', 'r-refund']
    ['r-72', 'r-61', 'r-TRANSACTION', 'w-checkout', 'r-void', 'r-void']
    ['r-41', 'r-order41']
    ['r-58', 'r-70', 'r-ACTION_TO_CONFIRM', 'w-70']
    ['r-67', 'r-96', 'w-96', 'r-TRANSACTION']
    """
    checkout_pks = list(range(100))
    num_txn = 10
    for _ in range(num_txn):
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
    txn = []

    fulfillment = Fulfillment()
    txn.append(f"r-{fulfillment_pk}")
    if fulfillment.warehouse:
        for line in fulfillment.lines:
            if line.order_line.variant and line.order_line.variant.track_inventory:
                txn.append(f"r-{line.order_line.pk}")
        txn.append(f"w-{fulfillment_pk}")
    txn.append(f"w-{fulfillment.lines}")

    return txn

def saleor_cancel_order_sim():
    """
    Example output:

    """
    fulfillment_pks = list(range(100))
    num_txn = 10
    for _ in range(num_txn):
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
    txn = []

    # Read order row from DB and lock it for update
    order = Order(order_pk)
    txn.append(f"r-{order_pk}")
    
    # Read payment row (associated with the order) and lock it for update
    payment = order.payment
    txn.append(f"r-{payment.pk}")
    
    # Validation: payment must be active and amount must be positive.
    if not payment.is_active:
        txn.append("validation-error: inactive payment")
    if amount <= 0:
        txn.append("validation-error: non-positive amount")
    
    # Perform the capture transaction via the payment gateway.
    # This call would normally create and record a new transaction.
    transaction = Transaction()  # Result from gateway.capture(payment, amount)
    txn.append(f"w-{transaction.pk}")  # Write operation: saving the transaction record
    
    # If the capture transaction succeeded, update order and payment statuses.
    if transaction.kind == "CAPTURE":
        # Read site settings row for update (e.g., for logging or additional validation)
        site = Site()
        txn.append(f"r-{site.pk}")
        
        # Write operations: updating order and payment statuses.
        txn.append(f"w-{order.pk}")    # Write operation: update order status to 'charged'
        txn.append(f"w-{payment.pk}")  # Write operation: update payment status (captured)

    return txn

def saleor_payment_order_sim():
    """
    Example output:

    """
    order_pks: int = list(range(100))
    amount: float = np.random.uniform(-10, 100)
    num_txn = 10
    for _ in range(num_txn):
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

              # For the order line, read the allocation and associated stock records
              allocation = SELECT * FROM Allocation WHERE order_line = order_line FOR UPDATE
              stock = SELECT * FROM Stock WHERE id = allocation.stock_id FOR UPDATE

              # Determine fulfillment quantity (e.g., random quantity)
              quantity = calculated quantity
              # Create a new fulfillment line record (write)
              INSERT INTO FulfillmentLine(fulfillment, order_line, quantity, stock)
              # Update order_line to set quantity_fulfilled (write)
              UPDATE OrderLine SET quantity_fulfilled = quantity WHERE id = order_line.id
              # Update allocation: reduce quantity_allocated (write)
              UPDATE Allocation SET quantity_allocated = quantity_allocated - quantity WHERE id = allocation.pk
              # Update stock: reduce quantity_allocated (write)
              UPDATE Stock SET quantity_allocated = quantity_allocated - quantity WHERE id = stock.pk

      txn.append("w-{order_id}")  # update order record with new status
    TRANSACTION COMMIT
    """
    txn = []
    
    # Read order record and lock for update
    txn.append(f"r-{order_id}")
    
    # Retrieve order lines (simulated from input_data)
    order_line_ids = input_data.get("order_line_ids", [])
    for line_id in order_line_ids:
        txn.append(f"r-{line_id}")
    
    # Process each order line
    for line in input_data.get("lines", []):
        warehouse_id = line.get("warehouse")
        txn.append(f"r-{warehouse_id}")
        
        # Simulate fulfillment decision and subsequent writes
        if line.get("fulfill", True):
            txn.append("rw-fulfillment")  # get_or_create fulfillment
            txn.append("r-allocation")
            txn.append("r-stock")
            txn.append("w-fulfillment_line")
            txn.append("w-order_line")       # update quantity_fulfilled
            txn.append("w-allocation")       # update allocation.quantity_allocated
            txn.append("w-stock")            # update stock.quantity_allocated     
    # Update the order status
    txn.append(f"w-{order_id}")
    
    return txn

def saleor_order_fulfill_sim():
    """
    Example output:

    """
    order_ids = list(range(100))
    num_txn = 10
    for _ in range(num_txn):
        num_lines = np.random.choice(range(1, 10))
        input_data = {
            "order_line_ids": [np.random.choice(order_ids) for _ in range(num_lines)],
            "lines": [{"warehouse": np.random.choice(order_ids), "fulfill": np.random.choice(True, False)} for _ in range(num_lines)]
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
    txn = []

    # Read order record (lock for update)
    txn.append(f"r-{order_id}")

    # Process each new order line from input_data
    for line in input_data.get("lines", []):
        variant_id = line.get("variant_id")
        # Read product variant record (lock for update)
        txn.append(f"r-{variant_id}")
        # Simulate writing a new order line record. Here we simulate an order line ID.
        order_line_id = f"line_{variant_id}"
        txn.append(f"w-{order_line_id}")

    # Create order event for added products
    txn.append("w-order_event")
    # Invalidate order prices
    txn.append(f"w-{order_id}")  # update should_refresh_prices field

    # Recalculate order weight
    for line in input_data.get("lines", []):
        order_line_id = f"line_{line.get('variant_id')}"
        txn.append(f"r-{order_line_id}")  # read each order line for weight calculation
    txn.append(f"w-{order_id}")  # Update order weight field

    txn.append(f"w-{order_id}") # Update search_vector field
    txn.append(f"w-{order_id}") # Save the order (final write)
    txn.append("w-order_event_status")     # Call event by order status (simulate writing order event status update)

    return txn

def saleor_order_lines_create_sim():
    """
    Example output:

    """
    order_ids = list(range(100))
    num_txn = 10
    for _ in range(num_txn):
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
    txn = []
    payment = Payment()
    checkout = Checkout()

    txn.append(f"r-{payment_intent.payment_intent_id}")
       
    if payment_intent.checkout_exists:
        txn.append(f"r-{payment.id}")

    # Re-read Payment with lock
    txn.append(f"r-{payment_intent.payment_intent_id}")
    txn.append(f"w-update_pmt_details-{payment.id}")

    if not payment_intent.payment_active:
        # Payment is inactive –> void/refund branch.
        txn.append(f"r-transaction-{payment.id}")
        txn.append(f"w-insert_into_transaction-{payment.id}")
        txn.append(f"w-update_payment-{payment.id}")
    elif payment_intent.payment_order_exists:
        if payment_intent.payment_charge_status_pending:
            txn.append(f"w-insert_into_transaction-{payment.id}")
    elif payment_intent.checkout_exists:
        # Processing via checkout branch.
        txn.append(f"r-{payment.id}")
        txn.append(f"w-insert_into_transaction-{payment.id}")
        txn.append(f"w-update_payment-{payment.id}")
        txn.append(f"r-{checkout.id}")
        txn.append(f"w-insert_into_order-{payment.order_id}")

    return txn

def saleor_stripe_handle_authorized_payment_intent_sim():
    """
    Example output:

    """
    payment_intents = [StripePaymentObj() for _ in range(10)]
    for payment_intent in payment_intents:
        result = saleor_stripe_handle_authorized_payment_intent_generator(payment_intent)
        print(result)

### OTHER TRANSACTIONS ###

# Skipped, too opaque
def saleor_payment_authorize():
    """
    Transaction 2
    Purpose: Coordinate concurrent payment processing.
    saleor/payment/gateway.py#authorize
    https://github.com/saleor/saleor/blob/c738dcc49f65750fa39e6cd5c619f89e50184894/saleor/payment/gateway.py#L302
    """

def saleor_payment_refund():
    """
    Transaction 4
    Purpose: Coordinate concurrent payment processing.
    saleor/order/actions.py#create_refund_fulfillment
    """

def saleor_get_payment_adyen():
    """
    Transaction 9
    Purpose: Coordinate concurrent payment processing.
    saleor/payment/gateways/adyen/webhooks.py#get_payment
    """

def saleor_get_checkout_adyen():
    """
    Transaction 10
    Purpose: Coordinate concurrent order processing.
    saleor/payment/gateways/adyen/webhooks.py#get_checkout
    """

def saleor_get_delete_categories():
    """
    Transaction 13
    Purpose: Coordinate concurrent categories updating.
    saleor/product/utils/__init__.py#delete_categories
    """

def saleor_get_order_line_update():
    """
    Transaction 14
    Purpose: Coordinate concurrent order updating.
    saleor/warehouse/management.py#OrderLineUpdate
    """

def main():
    # saleor_checkout_voucher_code_sim() # Transaction 1
    saleor_checkout_payment_process_sim() # Transaction 2

if __name__ == '__main__':
    main()