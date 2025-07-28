# oscar_transactions.py

class Transaction:
    def __init__(self):
        self.ops = []
        self.aborted = False
    def append_read(self, s): self.ops.append(('read', s))
    def append_write(self, s): self.ops.append(('write', s))
    def append_log(self, s): self.ops.append(('log', s))
    def append_signal(self, s): self.ops.append(('signal', s))
    def append_call(self, name, *args): self.ops.append(('call', name, args))
    def abort(self, reason=None):
        self.aborted = True
        self.append_log(f"Transaction aborted: {reason}")

# 1. ORDER PLACEMENT

def oscar_submit_order(user, basket, shipping_address, shipping_method, shipping_charge,
                       billing_address, order_total, payment_kwargs, order_kwargs, surcharges):
    """
    Purpose: Convert a basket into a submitted order
    Location: oscar/apps/checkout/views.py

    PSEUDOCODE:
    TRANSACTION START
    IF basket.is_tax_known = FALSE OR shipping_charge.is_tax_known = FALSE THEN
        ROLLBACK;
    order_number = generate_order_number(basket)
    set session.order_number = order_number
    UPDATE basket SET status = ‘FROZEN’ WHERE id = :basket_id;
    INSERT INTO session_data (key, value) VALUE (‘order_number’, :order_number);
    send signal pre_payment
    call handle_payment(order_number, order_total)
    IF payment fails THEN
        UPDATE basket SET status = 'OPEN' WHERE id = :basket_id;
        ROLLBACK;
    send signal post_payment
    call handle_order_placement(...)
    TRANSACTION COMMIT
    """
    t = Transaction()
    if not basket.is_tax_known or not shipping_charge.is_tax_known:
        t.abort("Tax unknown for basket or shipping charge")
        return t
    order_number = generate_order_number(basket)
    t.append_write(f"session.order_number({order_number})")
    t.append_write(f"basket[{basket.id}].status('FROZEN')")
    t.append_write(f"session_data['order_number'] = {order_number}")
    t.append_signal("pre_payment")
    payment_result = handle_payment(order_number, order_total)
    if not payment_result.success:
        t.append_write(f"basket[{basket.id}].status('OPEN')")
        t.abort("Payment failed; basket re-opened")
        return t
    t.append_signal("post_payment")
    t.append_call("handle_order_placement", order_number, user, basket, shipping_address, 
                  shipping_method, shipping_charge, billing_address, order_total, surcharges)
    return t

# 2. PAYMENT EVENT 

def oscar_create_payment_event(order, event_type, amount, lines=None, line_quantities=None, reference=None):
    """
    Purpose: Create a payment event for an order
    Location: oscar/apps/order/processing.py

    PSEUDOCODE:
    TRANSACTION START
    INSERT INTO order_paymentevent (order_id, event_type, amount, reference)
        VALUES (order.id, event_type, amount, reference)
    RETURNING id INTO event_id;
    IF lines AND line_quantities ARE PROVIDED:
        FOR EACH (line, quantity) IN zip(lines, line_quantities):
            INSERT INTO order_paymentevent_quantity (event_id, line_id, quantity)
                VALUES (event_id, line.id, quantity);
    TRANSACTION COMMIT
    """
    t = Transaction()
    t.append_write(f"order_paymentevent.add(order_id={order.id}, event_type={event_type}, amount={amount}, reference={reference})")
    event_id = "event_id"
    if lines and line_quantities:
        for line, quantity in zip(lines, line_quantities):
            t.append_write(f"order_paymentevent_quantity.add(event_id={event_id}, line_id={line.id}, quantity={quantity})")
    return t

# 3. STOCK: ALLOCATE

def oscar_allocate(stockrecord_id, quantity):
    """
    Purpose: Reserve stock for a purchase (allocate)
    Location: oscar/apps/partner/abstract_models.py

    PSEUDOCODE:
    TRANSACTION START
    UPDATE stock_record SET num_allocated = COALESCE(num_allocated, 0) + :quantity
        WHERE id = :stockrecord_id;
    REFRESH stock_record WHERE id = :stockrecord_id;
    TRANSACTION COMMIT
    """
    t = Transaction()
    t.append_read(f"stock_record[{stockrecord_id}].num_allocated")
    t.append_write(f"stock_record[{stockrecord_id}].num_allocated += {quantity}")
    t.append_read(f"stock_record[{stockrecord_id}]")
    return t

# 4. STOCK: CONSUME (FULFILLMENT)

def oscar_consume_allocation(stockrecord_id, quantity):
    """
    Purpose: Deduct reserved stock after shipment
    Location: oscar/apps/partner/abstract_models.py

    PSEUDOCODE:
    TRANSACTION START
    UPDATE stock_record
        SET num_allocated = COALESCE(num_allocated, 0) - :quantity,
            num_in_stock = COALESCE(num_in_stock, 0) - :quantity
        WHERE id = :stockrecord_id;
    REFRESH stock_record WHERE id = :stockrecord_id;
    TRANSACTION COMMIT
    """
    t = Transaction()
    t.append_read(f"stock_record[{stockrecord_id}].num_allocated")
    t.append_read(f"stock_record[{stockrecord_id}].num_in_stock")
    t.append_write(f"stock_record[{stockrecord_id}].num_allocated -= {quantity}")
    t.append_write(f"stock_record[{stockrecord_id}].num_in_stock -= {quantity}")
    t.append_read(f"stock_record[{stockrecord_id}]")
    return t

# 5. STOCK: CANCEL ALLOCATION

def oscar_cancel_allocation(stockrecord_id, quantity):
    """
    Purpose: Roll back a stock allocation
    Location: oscar/apps/partner/abstract_models.py

    PSEUDOCODE:
    TRANSACTION START
    UPDATE stock_record
        SET num_allocated = COALESCE(num_allocated, 0) - LEAST(COALESCE(num_allocated, 0), :quantity)
        WHERE id = :stockrecord_id;
    REFRESH stock_record WHERE id = :stockrecord_id;
    TRANSACTION COMMIT
    """
    t = Transaction()
    t.append_read(f"stock_record[{stockrecord_id}].num_allocated")
    t.append_write(f"stock_record[{stockrecord_id}].num_allocated = COALESCE(num_allocated, 0) - MIN(COALESCE(num_allocated, 0), {quantity})")
    t.append_read(f"stock_record[{stockrecord_id}]")
    return t

# 6. REFUND & RETURN

def oscar_create_refund_event(order, event_type, amount, lines=None, line_quantities=None):
    """
    Purpose: Create a refund event and restore stock for returned/refunded lines
    Location: oscar/apps/order/processing.py

    PSEUDOCODE:
    TRANSACTION START
    INSERT INTO order_refundevent (order, event_type, amount)
        VALUES (:order_id, :event_type, :amount)
    RETURNING id INTO event_id;
    IF lines AND line_quantities:
        FOR EACH (line, quantity) IN zip(lines, line_quantities):
            INSERT INTO order_refundevent_quantity (event_id, line_id, quantity)
                VALUES (event_id, line.id, quantity);
            IF line.product.is_stock_tracked:
                UPDATE stock_record SET num_in_stock = num_in_stock + quantity WHERE id = line.stockrecord_id;
    TRANSACTION COMMIT
    """
    t = Transaction()
    t.append_write(f"order_refundevent.add(order_id={order.id}, event_type={event_type}, amount={amount})")
    event_id = "event_id"
    if lines and line_quantities:
        for line, quantity in zip(lines, line_quantities):
            t.append_write(f"order_refundevent_quantity.add(event_id={event_id}, line_id={line.id}, quantity={quantity})")
            if line.product.is_stock_tracked:
                t.append_read(f"stock_record[{line.stockrecord_id}].num_in_stock")
                t.append_write(f"stock_record[{line.stockrecord_id}].num_in_stock += {quantity}")
    return t

# 7. ORDER CANCELLATION

def oscar_cancel_order(order):
    """
    Purpose: Cancel an order, restock goods, and void payment/voucher.
    Location: oscar/apps/order/processing.py

    PSEUDOCODE:
    TRANSACTION START
    UPDATE order SET status='cancelled' WHERE id=:order.id;
    FOR EACH line in order.lines:
        IF line.product.is_stock_tracked:
            UPDATE stock_record SET num_in_stock = num_in_stock + line.quantity WHERE id = line.stockrecord_id;
        UPDATE stock_record SET num_allocated = GREATEST(num_allocated - line.quantity, 0) WHERE id = line.stockrecord_id;
    UPDATE order_paymentevent SET status='voided' WHERE order_id = :order.id;
    UPDATE voucher SET num_orders = num_orders - 1 WHERE id IN (order.voucher_ids);
    TRANSACTION COMMIT
    """
    t = Transaction()
    t.append_write(f"order[{order.id}].status = 'cancelled'")
    for line in order.lines:
        if line.product.is_stock_tracked:
            t.append_read(f"stock_record[{line.stockrecord_id}].num_in_stock")
            t.append_write(f"stock_record[{line.stockrecord_id}].num_in_stock += {line.quantity}")
        t.append_read(f"stock_record[{line.stockrecord_id}].num_allocated")
        t.append_write(f"stock_record[{line.stockrecord_id}].num_allocated = max(num_allocated - {line.quantity}, 0)")
    t.append_write(f"order_paymentevent[order_id={order.id}].status = 'voided'")
    if getattr(order, 'voucher_ids', None):
        for vid in order.voucher_ids:
            t.append_read(f"voucher[{vid}].num_orders")
            t.append_write(f"voucher[{vid}].num_orders -= 1")
    return t

# 8. VOUCHER USAGE

def oscar_voucher_record_usage(voucher, order, user):
    """
    Purpose: Record the application of a voucher to an order
    Location: oscar/apps/voucher/abstract_models.py

    PSEUDOCODE:
    TRANSACTION START
    if user.is_authenticated:
        INSERT INTO voucher_application (voucher_id, order_id, user_id, date_created)
            VALUES (self.id, order.id, user.id, CURRENT_TIMESTAMP)
    else:
        INSERT INTO voucher_application (voucher_id, order_id, user_id, date_created)
            VALUES (self.id, order.id, NULL, CURRENT_TIMESTAMP)
    UPDATE voucher SET num_orders = num_orders + 1 WHERE id = self.id
    TRANSACTION COMMIT
    """
    t = Transaction()
    if user.is_authenticated:
        t.append_write(f"voucher_application.add(voucher_id={voucher.id}, order_id={order.id}, user_id={user.id}, date_created=now())")
    else:
        t.append_write(f"voucher_application.add(voucher_id={voucher.id}, order_id={order.id}, user_id=NULL, date_created=now())")
    t.append_read(f"voucher[{voucher.id}].num_orders")
    t.append_write(f"voucher[{voucher.id}].num_orders += 1")
    return t

# 9. BASKET MERGE

def oscar_merge_baskets(primary_basket, secondary_basket):
    """
    Purpose: Merge two baskets into one for a user
    Location: oscar/apps/basket/utils.py

    PSEUDOCODE:
    TRANSACTION START
    For each line in secondary_basket:
        If line's product in primary_basket:
            UPDATE basket_line in primary_basket: quantity += line.quantity
            DELETE basket_line in secondary_basket
        Else:
            UPDATE basket_line: move line from secondary to primary (set basket_id = primary.id)
    DELETE secondary_basket
    TRANSACTION COMMIT
    """
    t = Transaction()
    for line in secondary_basket.lines:
        if line.product in primary_basket.products:
            t.append_read(f"basket_line[{primary_basket.id},{line.product.id}].quantity")
            t.append_write(f"basket_line[{primary_basket.id},{line.product.id}].quantity += {line.quantity}")
            t.append_write(f"DELETE basket_line[{secondary_basket.id},{line.product.id}]")
        else:
            t.append_write(f"basket_line[{line.id}].basket_id = {primary_basket.id}")
    t.append_write(f"DELETE basket[{secondary_basket.id}]")
    return t

# 10. SHIPPING EVENT (FULFILLMENT)

def oscar_create_shipping_event(order, event_type, lines, line_quantities):
    """
    Purpose: Create a shipping event, mark goods as shipped, and deduct inventory.
    Location: oscar/apps/order/processing.py

    PSEUDOCODE:
    TRANSACTION START
    INSERT INTO order_shippingevent (order_id, event_type)
        VALUES (order.id, event_type)
    RETURNING id INTO event_id;
    FOR EACH (line, quantity) IN zip(lines, line_quantities):
        INSERT INTO order_shippingevent_quantity (event_id, line_id, quantity)
            VALUES (event_id, line.id, quantity);
        UPDATE stock_record
            SET num_allocated = COALESCE(num_allocated, 0) - quantity,
                num_in_stock = COALESCE(num_in_stock, 0) - quantity
            WHERE id = line.stockrecord_id;
    TRANSACTION COMMIT
    """
    t = Transaction()
    t.append_write(f"order_shippingevent.add(order_id={order.id}, event_type={event_type})")
    event_id = "event_id"
    for line, quantity in zip(lines, line_quantities):
        t.append_write(f"order_shippingevent_quantity.add(event_id={event_id}, line_id={line.id}, quantity={quantity})")
        t.append_read(f"stock_record[{line.stockrecord_id}].num_allocated")
        t.append_read(f"stock_record[{line.stockrecord_id}].num_in_stock")
        t.append_write(f"stock_record[{line.stockrecord_id}].num_allocated -= {quantity}")
        t.append_write(f"stock_record[{line.stockrecord_id}].num_in_stock -= {quantity}")
    return t

# (Optional) 11. ACCOUNT TRANSFER (if oscar_accounts is used)

def oscar_account_transfer(from_account_id, to_account_id, amount):
    """
    Purpose: Transfer credits between two Oscar accounts atomically.
    Location: oscar_accounts/...
    PSEUDOCODE:
    TRANSACTION START
    UPDATE oscar_account SET balance = balance - :amount WHERE id = :from_account_id;
    UPDATE oscar_account SET balance = balance + :amount WHERE id = :to_account_id;
    INSERT INTO oscar_transaction (from_id, to_id, amount, date);
    TRANSACTION COMMIT
    """
    t = Transaction()
    t.append_read(f"oscar_account[{from_account_id}].balance")
    t.append_write(f"oscar_account[{from_account_id}].balance -= {amount}")
    t.append_read(f"oscar_account[{to_account_id}].balance")
    t.append_write(f"oscar_account[{to_account_id}].balance += {amount}")
    t.append_write(f"oscar_transaction.add(from_id={from_account_id}, to_id={to_account_id}, amount={amount}, date=now())")
    return t

# End of oscar_transactions.py
