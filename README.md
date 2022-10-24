Lang: Python 3.9

Project type: console / no GUI

Project name: 

# NCR Aloha POS to UCS Storehouse v5 Data Import Utility.

- Aloha POS - https://www.ncr.com/restaurants/aloha-restaurant-pos-system
- Storehouse 5 - https://rkeeper.com/products/r_keeper/storehouse-5-skladskoy-uchet/

Goal: Get 'Aloha POS' (NCR) cash system data files:
- dictionary dbf-tables: CAT.DBF, CIT.DBF, CMP.DBF, ITM.DBF, TDR.DBF, RSN.DBF;
- shits dbf-tables: GNDITEM.DBF, GNDTNDR.DBF, GNDVOID.DBF;

and send dicts and goods expenditure trought SH5 WEB API v2 fuctionality to 'Storehouse v5'.

Project structure:
1. AlohaSh5.py - main functionality module;
2. AlohaSh5.ini - main config-file;
3. dbf_res.py - actions with aloha and sh dbf files (read, sort, filtering and write) module;
4. ini_res.py - actions with congig ini-file (read, write) module;
5. \AlohaTS\DATA - AlohaPOS Database (Dicts) sample;
6. \AlohaTS\YYYYMMDD - AlohaPOS Database (Shifts) samples;
7. \Docs\AlohaPOS_DBF.pdf - Grind export files documentation
