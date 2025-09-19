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


### Transaction 3 (Transaction 2 from Tang et al.) ###
def scmsuite_get_update_sql_generator(id: int) -> Transaction:
    """
    Transaction 2.
    Validation-based transaction.
    Purpose: Coordinate concurrent data updating
    com/doublechaintech/retailscm/CommonJDBCTemplateDAO.java#getUpdateSQL
    
    https://github.com/doublechaintech/scm-biz-suite/blob/82cc55dea9660beb478879040ebd31f32fd33109/bizcore/WEB-INF/retailscm_core_src/com/doublechaintech/retailscm/CommonJDBCTemplateDAO.java#L1060-L1073
    getUpdateSQL is called https://github.com/doublechaintech/scm-biz-suite/blob/82cc55dea9660beb478879040ebd31f32fd33109/bizcore/WEB-INF/retailscm_core_src/com/doublechaintech/retailscm/goodsshelf/GoodsShelfJDBCTemplateDAO.java#L812-L818
    PSEUDOCODE:
    In:
    TRANSACTION START
    SELECT * FROM GoodsShelf WHERE id = :id FOR UPDATE
    UPDATE GoodsShelf SET name = :name, position = :position, description = :description WHERE id = :id
    TRANSACTION COMMIT
    """
    t = Transaction()
    t.append_read(f"goods_shelf({id})")
    t.append_write(f"goods_shelf({id})")
    return t

def scmsuite_get_update_sql_sim(num_txn: int) -> list[str]:
    """
    Example output:

    ['r-goods_shelf(26)', 'w-goods_shelf(26)']
    ['r-goods_shelf(13)', 'w-goods_shelf(13)']
    ['r-goods_shelf(30)', 'w-goods_shelf(30)']
    ['r-goods_shelf(15)', 'w-goods_shelf(15)']
    ['r-goods_shelf(4)', 'w-goods_shelf(4)']
    ['r-goods_shelf(19)', 'w-goods_shelf(19)']
    ['r-goods_shelf(1)', 'w-goods_shelf(1)']
    ['r-goods_shelf(42)', 'w-goods_shelf(42)']
    ['r-goods_shelf(15)', 'w-goods_shelf(15)']
    ['r-goods_shelf(45)', 'w-goods_shelf(45)']
    """
    for _ in range(num_txn):
        id = np.random.randint(1, 50)
        result = scmsuite_get_update_sql_generator(id)
        print(result)


### Transaction 4 (Transaction 11 from Tang et al.) ###
def scmsuite_copy_catalog_form_generator(retail_store_id: int, catalog_id: int, catalog_version: int) -> Transaction:
    """
    Transaction 3.
    Lock-based transaction.
    RetailStoreCountryCenterManagerImpl.java#copyCatalogForm


    PSEUDOCODE:
    In:
    TRANSACTION START

    SELECT * FROM retail_store_country_center WHERE id = retailStoreCountryCenterId FOR UPDATE
    SELECT * FROM catalog WHERE id = catalogId AND version = catalogVersion;
    UPDATE retail_store_country_center SET catalog_list = modified_catalog_list WHERE id = retailStoreCountryCenterId;

    TRANSACTION COMMIT
    """
    t = Transaction()
    t.append_read(f"retail_store_id({retail_store_id})")
    t.append_read(f"catalog_id,catalog_version({catalog_id, catalog_version})")
    t.append_write(f"catalog_new_version({catalog_version+1})")
    return t

def scmsuite_copy_catalog_form_sim(num_txn: int) -> list[str]:
    """
    Example output:

    ['r-retail_store_id(14)', 'r-catalog_id,catalog_version((7, 1))', 'w-catalog_new_version(2)']
    ['r-retail_store_id(36)', 'r-catalog_id,catalog_version((23, 2))', 'w-catalog_new_version(3)']
    ['r-retail_store_id(40)', 'r-catalog_id,catalog_version((33, 9))', 'w-catalog_new_version(10)']
    ['r-retail_store_id(37)', 'r-catalog_id,catalog_version((16, 1))', 'w-catalog_new_version(2)']
    ['r-retail_store_id(4)', 'r-catalog_id,catalog_version((6, 8))', 'w-catalog_new_version(9)']
    ['r-retail_store_id(9)', 'r-catalog_id,catalog_version((8, 1))', 'w-catalog_new_version(2)']
    ['r-retail_store_id(15)', 'r-catalog_id,catalog_version((38, 8))', 'w-catalog_new_version(9)']
    ['r-retail_store_id(41)', 'r-catalog_id,catalog_version((25, 2))', 'w-catalog_new_version(3)']
    ['r-retail_store_id(37)', 'r-catalog_id,catalog_version((5, 7))', 'w-catalog_new_version(8)']
    ['r-retail_store_id(32)', 'r-catalog_id,catalog_version((36, 5))', 'w-catalog_new_version(6)']
    """

    for _ in range(num_txn):
        retail_store_id = np.random.randint(1, 50)
        catalog_id = np.random.randint(1, 50)
        catalog_version = np.random.randint(1, 10)
        result = scmsuite_copy_catalog_form_generator(retail_store_id, catalog_id, catalog_version)
        print(result)


### Transaction 5 (Transaction 10 from Tang et al.) ### 
def scmsuite_remove_catalog_list_generator(retail_store_id: int, catalog_id: int, catalog_version: int) -> Transaction:
    """
    Transaction 5.
    Lock-based transaction.
    RetailStoreCountryCenterManagerImpl.java#removeCatalogList
    https://github.com/doublechaintech/scm-biz-suite/blob/82cc55dea9660beb478879040ebd31f32fd33109/bizcore/WEB-INF/retailscm_core_src/com/doublechaintech/retailscm/retailstorecountrycenter/RetailStoreCountryCenterManagerImpl.java#L742-L765

    
    PSEUDOCODE:
    In:
    TRANSACTION START
    SELECT * FROM retail_store_country_center WHERE id = retailStoreCountryCenterId FOR UPDATE
    SELECT * FROM catalog WHERE id IN (catalogIds) AND owner_id = retailStoreCountryCenterId
    UPDATE retail_store_country_center SET version = version + 1 WHERE id = retailStoreCountryCenterId
    DELETE FROM catalog WHERE id IN (catalogIds)
    TRANSACTION COMMIT
    """
    t = Transaction()
    t.append_read(f"retail_store_id({retail_store_id})")
    t.append_read(f"catalog_id,catalog_version({catalog_id, catalog_version})")
    t.append_write(f"catalog_new_version({catalog_version+1})")
    t.append_write("catalog_delete")
    return t

def scmsuite_remove_catalog_list_sim(num_txn: int) -> list[str]:
    """
    Example output:
    ['r-retail_store_id(29)', 'r-catalog_id,catalog_version((34, 5))', 'w-catalog_new_version(6)', 'w-catalog_delete']
    ['r-retail_store_id(11)', 'r-catalog_id,catalog_version((8, 3))', 'w-catalog_new_version(4)', 'w-catalog_delete']
    ['r-retail_store_id(36)', 'r-catalog_id,catalog_version((27, 8))', 'w-catalog_new_version(9)', 'w-catalog_delete']
    ['r-retail_store_id(12)', 'r-catalog_id,catalog_version((5, 1))', 'w-catalog_new_version(2)', 'w-catalog_delete']
    ['r-retail_store_id(20)', 'r-catalog_id,catalog_version((43, 4))', 'w-catalog_new_version(5)', 'w-catalog_delete']
    ['r-retail_store_id(32)', 'r-catalog_id,catalog_version((2, 5))', 'w-catalog_new_version(6)', 'w-catalog_delete']
    ['r-retail_store_id(47)', 'r-catalog_id,catalog_version((30, 2))', 'w-catalog_new_version(3)', 'w-catalog_delete']
    ['r-retail_store_id(27)', 'r-catalog_id,catalog_version((5, 1))', 'w-catalog_new_version(2)', 'w-catalog_delete']
    ['r-retail_store_id(27)', 'r-catalog_id,catalog_version((19, 4))', 'w-catalog_new_version(5)', 'w-catalog_delete']
    ['r-retail_store_id(41)', 'r-catalog_id,catalog_version((46, 5))', 'w-catalog_new_version(6)', 'w-catalog_delete']
    """

    for _ in range(num_txn):
        retail_store_id = np.random.randint(1, 50)
        catalog_id = np.random.randint(1, 50)
        catalog_version = np.random.randint(1, 10)
        result = scmsuite_remove_catalog_list_generator(retail_store_id, catalog_id, catalog_version)
        print(result)


### The following functions no longer exist in the codebase ###

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
    num_txn_3 = 10
    num_txn_4 = 10
    num_txn_5 = 10

    # scmsuite_internal_save_retail_sim(num_txn_1) # Transaction 1
    # scmsuite_add_supply_order_sim(num_txn_2) # Transaction 6
    # scmsuite_get_update_sql_sim(num_txn_3) # Transaction 2
    # scmsuite_copy_catalog_form_sim(num_txn_4) # Transaction 11
    scmsuite_remove_catalog_list_sim(num_txn_5) # Transaction 10

if __name__ == '__main__':
    main()