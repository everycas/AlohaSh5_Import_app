import dbf
import pandas as pd
import datetime as dt


class AlohaSh5Dbf:

    def __init__(self):

        self.codepage = 'cp1251'
        self.now = dt.datetime.now()
        self.db_names = ['CAT.DBF', 'CIT.DBF', 'ITM.DBF', 'RSN.DBF', 'TDR.DBF', 'CMP.DBF']
        self.shift_names = ['GNDITEM.DBF', 'GNDTNDR.DBF', 'GNDVOID.DBF']

    def read(self, log: str, path: str, name: str):
        """ Opens aloha dbf and returns list of lists. PARAMS: log: log 'path/name'; path: aloha dict/shifts path;
            name: aloha dbf dicts file 'CAT.DBF', 'CIT.DBF', 'ITM.DBF', 'RSN.DBF', 'TDR.DBF', 'CMP.DBF';
            or aloha dbf shifts file - 'GNDITEM.DBF', 'GNDTNDR.DBF', 'GNDVOID.DBF' """

        try:
            file = f'{path}/{name}'
            table = dbf.Table(file, codepage=self.codepage)

        except Exception as Argument:
            with open(log, 'a') as log_file:
                log_file.write(f'{self.now.date(), self.now.time()}: dbf {name} read error - {str(Argument)}\n')
        else:
            with table.open(dbf.READ_ONLY):
                df = pd.DataFrame(table)

                if not df.empty:
                    if name == 'CAT.DBF':  # items categs
                        # res: [0:id, 3:name, 6:sales]
                        ll = [[item[0], item[3].rstrip()] for item in df.values.tolist() if item[6] == 'Y']

                    if name == 'CIT.DBF':  # items by categs
                        # res: [0:category, 2:itemid]
                        ll = [[item[2], item[0]] for item in df.values.tolist()]

                    if name == 'ITM.DBF':  # items
                        # res: [0:id, 5:longname, 37:price]
                        ll = [[item[0], item[5].rstrip(), item[37]] for item in df.values.tolist()]

                    if name == 'RSN.DBF':  # del reasons
                        # res: [0:id, 3:name]
                        ll = [[item[0], item[3].rstrip()] for item in df.values.tolist()]

                    if name == 'TDR.DBF':  # currencies
                        # res: [0:id, 3:name, 4:cash]
                        ll = [[item[0], item[3].rstrip(), item[4]] for item in df.values.tolist() if item[9] == 0]

                    if name == 'CMP.DBF':  # discs / markups
                        # res: [0:id, 4:name, 14:rate]
                        ll = [[item[0], item[4].rstrip()] for item in df.values.tolist() if item[14] == 1.0]

                    if name == 'GNDITEM.DBF':  # exp items
                        # res: [2:check, 3:item, 5:category, 15:price, 18:dob, 23:qnt, 25:discprice]
                        ll = [[item[2], item[18], item[3], item[23], item[15], item[25], item[5]] for item in
                             df.values.tolist()]  #  if item[15] >= 0

                    if name == 'GNDVOID.DBF' and not df.empty:  # exp by del reasons
                        # res: [2:check, 4:item, 5:price, 6:date, 10:reason, 11:inventory]
                        ll = [[item[2], item[6], item[4], item[5], item[10]] for item in df.values.tolist()]

                    if name == 'GNDSALE.DBF' and not df.empty:  # exp by sales params
                        # res: [1:check, 3:type, 4:typeid, 5:amount, 17:dob]
                        ll = [[item[1], item[3], item[4], item[5], item[17]] for item in df.values.tolist()]

                    if name == 'GNDTNDR.DBF':  # exp by pays
                        # res: [1:check, 4:type, 5:typeid]
                        ll = [[item[1], item[4], item[5]] for item in df.values.tolist() if item[4] != 11 and item[5]]



                    result = [list(map(lambda x: x, group)) for group in ll]

                    return result
                else:
                    return []




