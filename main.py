
import numpy as np

def broadleaf_cart_update_generator(num_txn: int,
                              avg_txn_len: int, 
                              cart_ids: list[int], 
                              item_ids: list[int]) -> list[list[str]]:
    output = []
    assert num_txn > 0
    assert avg_txn_len > 0
    assert len(cart_ids) > 0
    assert len(item_ids) > 0
    txn_lengths = [max(2, round(x)) for x in np.random.normal(avg_txn_len, 1, num_txn)]
    for i in range(num_txn):
        txn = []
        txn_len = txn_lengths[i]
        cart = np.random.choice(cart_ids, 1)
        items = np.random.choice(cart_ids, txn_len - 1)
        txn.append(f"r-{cart[0]}")
        for item in items:
            txn.append(f"w-{item}")
        output.append(txn)
    return output

def broadleaf_cart_update_sim():
    num_txn = 10
    avg_txn_len = 5
    cart_ids = list(range(10))
    item_ids = list(range(100))
    sim_results = broadleaf_cart_update_generator(num_txn, avg_txn_len, cart_ids, item_ids)
    for r in sim_results:
        print(r)

def main():
    broadleaf_cart_update_sim()
    
if __name__ == "__main__":
    main()