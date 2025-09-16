Guide to prompt to create csv file

There are four input in the database
Transaction_ID
LORRY_ID
WEIGHT
DELIVERY_TIME


TRNASCTION_ID
Transaction_ID per transaction
A transaction is one lorry delivering one load per day

LORRY_ID
Lorry_ID which is the vehice idetifier which is the vehicle license plate

Lorry has 5 types and the qty stated below
- tipper, 20 qty
- roro , 15 qty 
- lifter, 15 qty 
- dumper, 15 qty 
- open, 15 qty 
- compactor, 20 qty 

The fleet has 80 trucks in total with unique license plate number sequenes as follows:
P**_zzzz where are ** are random letteres between aa to zz and zzzz are random four digit numbers from 1234 to 7890
Once the 80 trucks have each inidividual license plate, it becomes their unique identifier

WEIGHT
Weight are weight of each truck delivery based on their capacity
- tipper has 1.5 tons capacity each
- roro has 5.0 tons  capacity each
- lifter has 5.0 tons capacity each
- dumper has 5.0 ton capacity each
- open has 5.0 tons capacity each
- compactor has 10.0 tons capacity each

DEELIVERY_TIME
Delivery Time and Date in Date, Day, Hours, Minutes
Each truck makes one delivery every day bewteen 1st Januanru 2025 to 31st January 2025