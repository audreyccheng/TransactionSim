# https://github.com/doublechaintech/scm-biz-suite
# Implements ad hoc transactions via the synchronized keyword
# Total of 11 transactions on https://project-concerto.github.io

# References from Tang et al paper:
# [90] Philip Z. 2021. Comments on issue 17 (in Chinese). https://github.com/
# doublechaintech/scm-biz-suite/issues/17
# [91] Xiaodong Zhang. 2021. The synchronized used to prevent concurrency doesn’t
# work as expected in Chinese). 

import numpy as np
from transaction import Transaction

#################################
####   Simulator functions   ####
#################################

### Transaction 1 (Transaction 1 from Tang et al.) ###
def scmsuite_internal_save_retail_generator(changed: bool, retail_store_id: int) -> Transaction:
    """
    Transaction 1.
    Lock-based transaction.
    Purpose: Coordinate concurrent data updating
    RetailStoreCountryCenterManagerImpl.java#internalSaveRetailStoreCountryCenter
    
    https://github.com/doublechaintech/scm-biz-suite/blob/82cc55dea9660beb478879040ebd31f32fd33109/bizcore/WEB-INF/retailscm_core_src/com/doublechaintech/retailscm/retailstorecountrycenter/RetailStoreCountryCenterManagerImpl.java#L383-L402
    PSEUDOCODE:
    In: changed: bool, retail_store_id: int
    TRANSACTION START
    SELECT * FROM RetailStoreCountryCenter WHERE id = :retailStoreCountryCenter.id FOR UPDATE
    if changed:
        INSERT INTO RetailStoreCountryCenter (id, name, ...) VALUES (:id, :name, ...) ON DUPLICATE KEY UPDATE values
    TRANSACTION COMMIT
    """
    t = Transaction()
    t.append_read(f"retail_store_id({retail_store_id})")
    if changed:
        t.append_write(f"retail_store_id({retail_store_id})")
    return t

def scmsuite_internal_save_retail_sim(num_txn: int) -> list[str]:
    """
    Example output:

    ['r-retail_store_id(32)', 'w-retail_store_id(32)']
    ['r-retail_store_id(28)']
    ['r-retail_store_id(4)']
    ['r-retail_store_id(42)']
    ['r-retail_store_id(27)', 'w-retail_store_id(27)']
    ['r-retail_store_id(37)', 'w-retail_store_id(37)']
    ['r-retail_store_id(28)', 'w-retail_store_id(28)']
    ['r-retail_store_id(35)']
    ['r-retail_store_id(3)']
    ['r-retail_store_id(27)']
    """
    for _ in range(num_txn):
        changed = np.random.choice([True, False], p=[0.2, 0.8])
        retail_store_id = np.random.randint(1, 50)
        result = scmsuite_internal_save_retail_generator(changed, retail_store_id)
        print(result)

### Transaction 2 (Transaction 6 from Tang et al.) ###
def scmsuite_add_supply_order_generator(retail_store_country_center_id: int, total_amount: float) -> Transaction:
    """
    Transaction 6.
    Lock-based transaction.
    Purpose: Coordinate concurrent data updating
    RetailStoreCountryCenterManagerImpl.java#addXXX
    
    # Note that seller_id, title, contract are not included as they are keys for contention
    addSupplyOrder
    https://github.com/doublechaintech/scm-biz-suite/blob/82cc55dea9660beb478879040ebd31f32fd33109/bizcore/WEB-INF/retailscm_core_src/com/doublechaintech/retailscm/retailstorecountrycenter/RetailStoreCountryCenterManagerImpl.java#L2776-L2810
    PSEUDOCODE:
    In: retailStoreCountryCenterId: int, totalAmount: float
    TRANSACTION START
    # checkParamsForAddingSupplyOrder
    SELECT id FROM RetailStoreCountryCenter WHERE id = retailStoreCountryCenterId

    # loadRetailStoreCountryCenter
    SELECT * FROM RetailStoreCountryCenter WHERE id = retailStoreCountryCenterId FOR UPDATE

    INSERT INTO SupplyOrder (seller_id, title, contract, total_amount, retail_store_country_center_id) VALUES (:totalAmount, :retailStoreCountryCenterId)
    TRANSACTION COMMIT
    """
    t = Transaction()
    t.append_read(f"check_params({retail_store_country_center_id})")
    t.append_read(f"retail_store_country_center_id({retail_store_country_center_id})")
    t.append_write(f"total_amount({total_amount})")
    return t

def scmsuite_add_supply_order_sim(num_txn: int) -> list[str]:
    """
    Example output:

    ['r-check_params(21)', 'r-retail_store_country_center_id(21)', 'w-total_amount(35.01)']
    ['r-check_params(45)', 'r-retail_store_country_center_id(45)', 'w-total_amount(73.91)']
    ['r-check_params(28)', 'r-retail_store_country_center_id(28)', 'w-total_amount(70.52)']
    ['r-check_params(23)', 'r-retail_store_country_center_id(23)', 'w-total_amount(47.1)']
    ['r-check_params(47)', 'r-retail_store_country_center_id(47)', 'w-total_amount(83.11)']
    ['r-check_params(43)', 'r-retail_store_country_center_id(43)', 'w-total_amount(35.78)']
    ['r-check_params(24)', 'r-retail_store_country_center_id(24)', 'w-total_amount(49.58)']
    ['r-check_params(33)', 'r-retail_store_country_center_id(33)', 'w-total_amount(3.93)']
    ['r-check_params(43)', 'r-retail_store_country_center_id(43)', 'w-total_amount(61.11)']
    ['r-check_params(39)', 'r-retail_store_country_center_id(39)', 'w-total_amount(30.23)']
    """
    for _ in range(num_txn):
        retail_store_country_center_id = np.random.randint(1, 50)
        total_amount = round(np.random.uniform(0, 100), 2)
        result = scmsuite_add_supply_order_generator(retail_store_country_center_id, total_amount)
        print(result)

# Other functions

# 7 lock-based	RetailStoreCountryCenterManagerImpl.java#updateXXX	
# 8 lock-based	RetailStoreCountryCenterManagerImpl.java#updateXXX
# 9 lock-based	RetailStoreCountryCenterManagerImpl.java#removeXXX
# 10 lock-based	RetailStoreCountryCenterManagerImpl.java#removeXXXList
# 11 lock-based	RetailStoreCountryCenterManagerImpl.java#copyXXXForm	

# The following 3 functions are validation-based transactions and don't have r/w operations to a database.
def scmsuite() -> Transaction:
    """
    Transaction 2.
    Validation-based transaction.
    Purpose: Coordinate concurrent data updating
    com/doublechaintech/retailscm/CommonJDBCTemplateDAO.java#getUpdateSQL
    
    https://github.com/doublechaintech/scm-biz-suite/blob/82cc55dea9660beb478879040ebd31f32fd33109/bizcore/WEB-INF/retailscm_core_src/com/doublechaintech/retailscm/CommonJDBCTemplateDAO.java#L1060-L1073
    PSEUDOCODE:
    In:
    TRANSACTION START

    TRANSACTION COMMIT
    """
    t = Transaction()
    return t

def scmsuite() -> Transaction:
    """
    Transaction 3.
    Validation-based transaction.
    Purpose: Coordinate concurrent data updating
    com/doublechaintech/retailscm/CommonJDBCTemplateDAO.java#getDeleteSQL
    
    PSEUDOCODE:
    In:
    TRANSACTION START

    TRANSACTION COMMIT
    """
    t = Transaction()
    return t

def scmsuite() -> Transaction:
    """
    Transaction 4.
    Validation-based transaction.
    Purpose: Coordinate concurrent data updating
    com/doublechaintech/retailscm/CommonJDBCTemplateDAO.java#getDeleteWithVersionSQL
    
    PSEUDOCODE:
    In:
    TRANSACTION START

    TRANSACTION COMMIT
    """
    t = Transaction()
    return t

# This function no longer exists in the codebase
def scmsuite() -> Transaction:
    """
    Transaction 5.
    Lock-based transaction.
    Purpose: Coordinate concurrent data updating
    RetailStoreCountryCenterManagerImpl.java#breakWithRetailStoreByXXX
    
    PSEUDOCODE:
    In:
    TRANSACTION START

    TRANSACTION COMMIT
    """
    t = Transaction()
    return t

def main():
    """
    Generate SCM Suite transaction traces.
    """
    # Number of transactions to simulate per transaction type
    num_txn_1 = 10
    num_txn_2 = 10

    # scmsuite_internal_save_retail_sim(num_txn_1) # Transaction 1
    scmsuite_add_supply_order_sim(num_txn_2) # Transaction 6

if __name__ == '__main__':
    main()