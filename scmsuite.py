# https://github.com/doublechaintech/scm-biz-suite
# Implements ad hoc transactions via the synchronized keyword
# Total of 11 transactions on https://project-concerto.github.io

# References from Tang et al paper:
# [90] Philip Z. 2021. Comments on issue 17 (in Chinese). https://github.com/
# doublechaintech/scm-biz-suite/issues/17
# [91] Xiaodong Zhang. 2021. The synchronized used to prevent concurrency doesn’t
# work as expected in Chinese). 

import numpy as np
import datetime
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
    In:
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


# Other functions


# validation-based	com/doublechaintech/retailscm/CommonJDBCTemplateDAO.java#getUpdateSQL	Coordinate concurrent data updating	
# validation-based	com/doublechaintech/retailscm/CommonJDBCTemplateDAO.java#getDeleteSQL	Coordinate concurrent data updating	
# validation-based	com/doublechaintech/retailscm/CommonJDBCTemplateDAO.java#getDeleteWithVersionSQL	Coordinate concurrent data updating
# lock-based	RetailStoreCountryCenterManagerImpl.java#breakWithRetailStoreByXXX	Coordinate concurrent data updating
# lock-based	RetailStoreCountryCenterManagerImpl.java#addXXX	Coordinate concurrent data updating	
# lock-based	RetailStoreCountryCenterManagerImpl.java#updateXXX	Coordinate concurrent data updating	
# lock-based	RetailStoreCountryCenterManagerImpl.java#updateXXXProperty	Coordinate concurrent data updating
# lock-based	RetailStoreCountryCenterManagerImpl.java#removeXXX	Coordinate concurrent data updating
# lock-based	RetailStoreCountryCenterManagerImpl.java#removeXXXList	Coordinate concurrent data updating
# lock-based	RetailStoreCountryCenterManagerImpl.java#copyXXXForm	Coordinate concurrent data updating

def main():
    """
    Generate SCM Suite transaction traces.
    """
    # Number of transactions to simulate per transaction type
    num_txn_1 = 10

    scmsuite_internal_save_retail_sim(num_txn_1) # Transaction 1

if __name__ == '__main__':
    main()