from dbf_res import AlohaSh5Dbf
from ini_res import Ini
from operator import itemgetter
from itertools import groupby, tee
import datetime as dt
import requests
import os

# Objects
DBF = AlohaSh5Dbf()
INI = Ini()

# Names
LOG_NAME = 'AlohaSH5.log'
INI_NAME = 'AlohaSH5.ini'

# Today date and time
DT_NOW = dt.datetime.now()

# Aloha paths
INI_DB_PATH = INI.get(log=LOG_NAME, ini=INI_NAME, section='ALOHA_PATHS', param='db')
INI_SHIFTS_PATH = INI.get(log=LOG_NAME, ini=INI_NAME, section='ALOHA_PATHS', param='shifts')

# Aloha actual DB dbf-files to lists
DB_CAT = DBF.read(log=LOG_NAME, path=INI_DB_PATH, name='CAT.DBF')  # Categs
DB_CIT = DBF.read(log=LOG_NAME, path=INI_DB_PATH, name='CIT.DBF')  # Links items to categs
DB_CMP = DBF.read(log=LOG_NAME, path=INI_DB_PATH, name='CMP.DBF')  # Discounts / Markups
DB_ITM = DBF.read(log=LOG_NAME, path=INI_DB_PATH, name='ITM.DBF')  # Goods items
DB_RSN = DBF.read(log=LOG_NAME, path=INI_DB_PATH, name='RSN.DBF')  # Order del_reasons
DB_TDR = DBF.read(log=LOG_NAME, path=INI_DB_PATH, name='TDR.DBF')  # Pay_types / Currencies

# SH5 WEB API PARAMS
INI_HOST = INI.get(log=LOG_NAME, ini=INI_NAME, section='SH5_WEB_API', param='host')
INI_PORT = INI.get(log=LOG_NAME, ini=INI_NAME, section='SH5_WEB_API', param='port')
INI_USER = INI.get(log=LOG_NAME, ini=INI_NAME, section='SH5_WEB_API', param='user')
INI_PASS = INI.get(log=LOG_NAME, ini=INI_NAME, section='SH5_WEB_API', param='pass')

# SH5 GTREE ROOT GUID
INI_GGROUPS_ROOT_GUID = INI.get(log=LOG_NAME, ini=INI_NAME, section='SH5_GOODS_GROUP_ROOT', param='guid')

# DEFAULT_SUNIT ---------------->
INI_SUNIT_DEFAULT_NAME = INI.get(log=LOG_NAME, ini=INI_NAME, section='SH5_DEFAULT_SUNIT_NAME', param='sunit')
SUNIT_DEFAULT_GUID = '{00000000-0000-0000-0000-900000000000}'

# PAY_TYPES ---------------------------------->

# Cash
INI_CASH_NAME = INI.get(log=LOG_NAME, ini=INI_NAME, section='SH5_PAY_TYPES_NAMES', param='cash')
CASH_PTYPE_GUID = '{00000000-0000-0000-0000-110000000000}'
# Non_cash
INI_NON_CASH_NAME = INI.get(log=LOG_NAME, ini=INI_NAME, section='SH5_PAY_TYPES_NAMES', param='non_cash')
NON_CASH_PTYPE_GUID = '{00000000-0000-0000-0000-120000000000}'
# Cmp
INI_CMP_PAYS_NAME = INI.get(log=LOG_NAME, ini=INI_NAME, section='SH5_PAY_TYPES_NAMES', param='cmp_pays')
CMP_PTYPE_GUID = '{00000000-0000-0000-0000-130000000000}'
# Sell
INI_SELL_NAME = INI.get(log=LOG_NAME, ini=INI_NAME, section='SH5_PAY_TYPES_NAMES', param='sell')
SELL_GUID = '{00000000-0000-0000-0000-100000000000}'
# Refund
INI_REFUND_NAME = INI.get(log=LOG_NAME, ini=INI_NAME, section='SH5_PAY_TYPES_NAMES', param='refund')
REFUND_GUID = '{00000000-0000-0000-0000-140000000000}'

# CURRENCIES + CMP ------------>
CUR_RATE = 200000000000
# DEL_REASONS ---------->
RSN_RATE = 300000000000

# EXPENDITURE DOCS GROUPING / FILTERING OPTIONS
INI_GROUPS = INI.get(log=LOG_NAME, ini=INI_NAME, section='SH5_EXP_DOCS', param='groups')
INI_TOTALS = INI.get(log=LOG_NAME, ini=INI_NAME, section='SH5_EXP_DOCS', param='totals')
INI_SUNITS = INI.get(log=LOG_NAME, ini=INI_NAME, section='SH5_EXP_DOCS', param='sunits')
INI_REFUNDS = INI.get(log=LOG_NAME, ini=INI_NAME, section='SH5_EXP_DOCS', param='refunds')
INI_VOIDS = INI.get(log=LOG_NAME, ini=INI_NAME, section='SH5_EXP_DOCS', param='voids')
INI_RSN_CODES = INI.get(log=LOG_NAME, ini=INI_NAME, section='SH5_EXP_DOCS', param='rsn_codes_list').split(', ')


def api_request(proc_json):

    """ SH5 WEB API: exec_request function - sh5exec. """

    try:
        request = requests.post(url=f'http://{INI_HOST}:{INI_PORT}/api/sh5exec', json=proc_json)
        request.raise_for_status()
        data = request.json()
    except Exception as Argument:
        print(f'web_api_request_sh5 / Connection error: {str(Argument)}\n')
    else:
        # print(data)
        with open(LOG_NAME, 'a') as log_file:
            log_file.write(f'{DT_NOW} -> api_request: {proc_json}\n{data}\n\n')


def get_period():

    """ Get/return start/stop period """

    # Check shifts folder and create all shifts list
    shifts_path = INI.get(log=LOG_NAME, ini=INI_NAME, section='ALOHA_PATHS', param='shifts')

    shifts_list = []  # лист всех каталогов смен
    for root, dirs, files in os.walk(shifts_path):
        for d in dirs:
            if len(d) == 8 and d.isdigit():  # проверка длины каталога и на цифровое название
                shifts_list.append(d)  # лист каталогов: ['20211212', '20211213']

    print(f'Full shifts list: {shifts_list}')

    # Select work mode: if ini[MODE]auto = '1' then result will contain yesterday date only
    # if ini[MODE]auto = '0' then result will contain those dates that was entered in console
    auto_mode = INI.get(log=LOG_NAME, ini=INI_NAME, section='MODE', param='auto')

    if auto_mode == '0':

        # First and last folder date in shifts folder
        first_fldr_date = f'{shifts_list[0][6:]}.{shifts_list[0][4:6]}.{shifts_list[0][:4]}'
        last_fldr_date = f'{shifts_list[-1][6:]}.{shifts_list[-1][4:6]}.{shifts_list[-1][:4]}'

        # Print information about all possible data for import
        print(f'Shifts_folder contain data: from {first_fldr_date} to {last_fldr_date}')

        # Start date entering checking -------------------------------------------------->
        is_start_date_correct = False
        while not is_start_date_correct:
            # Input start date
            start_enter = input('Enter start_date / dd.mm.yyyy: ')
            start_day = start_enter[:2]
            start_month = start_enter[3:5]
            start_year = start_enter[6:]
            start_date_print_string = f'{start_day}.{start_month}.{start_year}'
            # Checking start date is_numeric
            if not start_day.isnumeric() or not start_month.isnumeric() or not start_year.isnumeric():
                print(f'Wrong start_date string {start_date_print_string}. Fix and try again.')
            else:
                # Checking start day, month, year for correct range
                if 32 > int(start_day) > 0 and 13 > int(start_month) > 0 and 2100 > int(start_year) > 1900:

                    # Start date RESULT string (shift folder name)
                    start_date_result_string = f'{start_year}{start_month}{start_day}'

                    # Checking date for presents in shifts folder
                    if start_date_result_string not in shifts_list:
                        print(f'Wrong start_date. No such date in shifts_folder. Fix and try again.')
                    else:
                        # Stop looping
                        is_start_date_correct = True
                else:
                    print(f'Wrong day, month or year number: {start_date_print_string}. Fix and try again.')

        # Stop date entering checking -------------------------------------------------->
        is_stop_date_correct = False
        while not is_stop_date_correct:
            # Input stop date
            stop_enter = input('Enter stop_date / dd.mm.yyyy: ')
            stop_day = stop_enter[:2]
            stop_month = stop_enter[3:5]
            stop_year = stop_enter[6:]
            stop_date_print_string = f'{stop_day}.{stop_month}.{stop_year}'
            # Checking stop date is_numeric
            if not stop_day.isnumeric() or not stop_month.isnumeric() or not stop_year.isnumeric():
                print(f'Wrong stop_date string {stop_date_print_string}. Fix and try again.')
            else:
                # Checking stop day, month, year for correct range
                if 32 > int(stop_day) > 0 and 13 > int(stop_month) > 0 and 2100 > int(stop_year) > 1900:

                    # Stop date RESULT string (shift folder name)
                    stop_date_result_string = f'{stop_year}{stop_month}{stop_day}'

                    # Checking date for presents in shifts folder
                    if stop_date_result_string not in shifts_list:
                        print(f'Wrong stop_date. No such date in shifts_folder. Fix and try again.')
                    else:
                        # Checking that stop_date is higher than start_date
                        if int(stop_date_result_string) < int(start_date_result_string):
                            print(f'Wrong period: {start_date_print_string}>{stop_date_print_string}. Fix and try again.')
                        else:
                            # Stop looping
                            is_stop_date_correct = True
                else:
                    print(f'Wrong day, month or year number: {stop_date_print_string}. Fix and try again.')

        print(f'Selected period: from {start_date_print_string} to {stop_date_print_string}')

        # Get selected dates list indexes
        start_index = shifts_list.index(start_date_result_string)
        stop_index = shifts_list.index(stop_date_result_string)

        # Result list
        result = shifts_list[start_index: stop_index + 1]
        return result

    elif auto_mode == '1':

        yesterday = str(DT_NOW.date() - dt.timedelta(days=1))
        yesterday_date_string = f'{yesterday[:4]}{yesterday[5:7]}{yesterday[8:10]}'

        if yesterday_date_string not in shifts_list:

            print('There is no yesterday_data in shifts_folder.')

            last_shift = f'{shifts_list[-1][6:8]}.{shifts_list[-1][4:6]}.{shifts_list[-1][:4]}'
            print(f'Will be taken last accessible shift {last_shift}.')

            return [shifts_list[-1]]

        else:

            yesterday_shift = f'{yesterday_date_string[6:8]}.{yesterday_date_string[4:6]}.{yesterday_date_string[:4]}'
            print(f'Yesterday shift {yesterday_shift} found - Ok!')

            return [yesterday_date_string]

    else:
        return [shifts_list[-1]]


def to_guid(num: str):

    """ Convert any number to SH5 guid """

    zero_add = ''
    guid_mask = '{00000000-0000-0000-0000-'
    postfix = '}'

    if len(num) < 12:
        diff = 12 - len(num)  # 6
        for _ in range(diff):
            zero_add += '0'
            code = zero_add + num
    elif len(num) > 12:
        diff = len(num) - 12
        code = num[diff:]
    else:
        code = num

    result = guid_mask + code + postfix
    return result


def ggroups_json():

    """ Aloha sales_categs from CAT.DBF convert to sh5_goods_groups_tree_json. """

    # Json params:
    parent_guid = []
    ggroup_guid = []
    ggroup_name = []
    # Fill params:
    for ggroup in DB_CAT:  # [id: int, name, sales]
        parent_guid.append(INI_GGROUPS_ROOT_GUID)
        ggroup_guid.append(to_guid(num=str(ggroup[0])))
        ggroup_name.append(ggroup[1])

    # Redy ggroups_json:
    repl_ggroups = {
        "UserName": INI_USER,
        "Password": INI_PASS,
        "ProcName": 'ReplGGroups',
        "Input": [
            {
                "Head": "209#2",
                "Original": ['209#3\\4', '4', '3'],
                "Values": [parent_guid, ggroup_guid, ggroup_name]
            }
        ]
    }
    return repl_ggroups


def goods_json():

    """ Aloha items from ITM.DBF and categ_links from CAT.DBF and CIT.DBF convert to sh5_goods_json. """

    # Filtering and sorting
    cits = sorted([item for item in DB_CIT if item[1] in [categ[0] for categ in DB_CAT]])  # [[int, int]]
    items = sorted(DB_ITM)
    # Zip cits and items to one common list (add sales categs as goods_parents)
    goods = []
    for item in items:  # [id, longname, price]
        for cit in cits:
            if item[0] == cit[0]:
                item.append(cit[1])
        goods.append(item)  # [id: int, name: str, price: float, parent: int]

    # Json params
    good_parent_guid = []  # guid: str
    good_guid = []  # guid: str
    good_name = []  # str
    good_price = []  # sale price + taxes: float
    good_rkcode = []  # int
    # Fill params
    for good in goods:
        good_parent_guid.append(to_guid(str(good[3])))
        good_guid.append(to_guid(num=str(good[0])))
        good_name.append(good[1])
        good_price.append(good[2])
        good_rkcode.append(good[0])

    # Redy goods_json
    repl_goods = {
        "UserName": INI_USER,
        "Password": INI_PASS,
        "ProcName": 'ReplGoods',
        "Input": [
            {
                "Head": "210",
                "Original": ['209\\4', '4', '3', '56', '241'],
                "Values": [good_parent_guid, good_guid, good_name, good_price, good_rkcode]
            }
        ]
    }
    return repl_goods


def corrs_json():

    """ Aloha items from CMP.DBF, RSN.DBF, TDR.DBF + other correspondents from ini convert to sh5_corrs_json. """

    # Json params
    corr_guid = []
    corr_name = []
    corr_type = []
    # CURRS: Add discounts / markups from CMP to corrs lists
    for cmp in DB_CMP:
        corr_guid.append(to_guid(str(cmp[0] + CUR_RATE)))  # str
        corr_name.append(cmp[1])  # str
        corr_type.append(2)  # int
    # CURRS: Add currencies from TDR to corrs lists
    for cur in DB_TDR:
        corr_guid.append(to_guid(str(cur[0] + CUR_RATE)))  # str
        corr_name.append(cur[1])  # str
        corr_type.append(2)  # int
    # DEL_REASONS: Add order_delete_reasons from RSN to corrs lists
    for rsn in DB_RSN:
        corr_guid.append(to_guid(str(rsn[0] + RSN_RATE)))  # str
        corr_name.append(rsn[1])  # str
        corr_type.append(2)  # int

    # PTYPE_CASH: Add cash_pay_type from ini to corrs lists
    corr_guid.append(CASH_PTYPE_GUID)  # str
    corr_name.append(INI_CASH_NAME)  # str
    corr_type.append(2)  # int
    # PTYPE_NON_CASH: Add non_cash_pay_type from ini to corrs lists
    corr_guid.append(NON_CASH_PTYPE_GUID)  # str
    corr_name.append(INI_NON_CASH_NAME)  # str
    corr_type.append(2)  # int
    # PTYPE_CMP_PAYS: Add cmp_pay_type from ini to corrs_list
    corr_guid.append(CMP_PTYPE_GUID)  # str
    corr_name.append(INI_CMP_PAYS_NAME)  # str
    corr_type.append(2)  # int

    # REFUND: Add refund from ini to corrs lists
    corr_guid.append(REFUND_GUID)  # str
    corr_name.append(INI_REFUND_NAME)  # str
    corr_type.append(2)  # int
    # SELLS: Add sell from ini to corrs lists
    corr_guid.append(SELL_GUID)  # str
    corr_name.append(INI_SELL_NAME)  # str
    corr_type.append(2)  # int

    # Redy corrs_json
    repl_corrs = {
        "UserName": INI_USER,
        "Password": INI_PASS,
        "ProcName": 'ReplCorrs',
        "Input": [
            {
                "Head": "107",
                "Original": ['4', '3', '32'],
                "Values": [corr_guid, corr_name, corr_type]
            }
        ]
    }
    return repl_corrs


def sunits_json():

    """ Aloha sell categs from CAT.DBF to sh5_sunits_json. """

    # Json params
    sunit_guid = []
    sunit_name = []

    # Append default sunit
    sunit_guid.append(SUNIT_DEFAULT_GUID)
    sunit_name.append(INI_SUNIT_DEFAULT_NAME)

    for sunit in DB_CAT:
        sunit_guid.append(to_guid(str(sunit[0])))
        sunit_name.append(sunit[1])

    # Redy sunits_json
    repl_sunits = {
        "UserName": INI_USER,
        "Password": INI_PASS,
        "ProcName": 'ReplSUnits',
        "Input": [
            {
                "Head": "226",
                "Original": ['4', '3'],
                "Values": [sunit_guid, sunit_name]
            }
        ]
    }
    return repl_sunits


def odocs_json(period: list):

    """ Expenditure from Aloha shifts files GNDITEM.DBF, GNDTNDR.DBF, GNDVOID.DBF to sh5 odocs_json. """

    # Json_params_lists to fill
    date = []
    sunit_guid = []
    good_guid = []
    good_qnt = []
    spec = []
    good_total = []
    corr_guid = []

    # MAIN SHIFT LOOP --->

    for shift_num in period:  # Shifts_lists by selected period

        tndr = DBF.read(log=LOG_NAME, path=f'{INI_SHIFTS_PATH}/{shift_num}', name='GNDTNDR.DBF')
        item = DBF.read(log=LOG_NAME, path=f'{INI_SHIFTS_PATH}/{shift_num}', name='GNDITEM.DBF')
        void = DBF.read(log=LOG_NAME, path=f'{INI_SHIFTS_PATH}/{shift_num}', name='GNDVOID.DBF')

        # SORT AND REFORMAT ITEMS ------------------------------------->

        def get_items(item_list: list, tndr_list: list):

            """ Prepare selected and grouping items_list using ini[SH5_EXP_DOCS] grouping / filtering params """

            all_currs = []  # cur_id, cur_name, cur_ptype_guid

            # Add currs_ptype_guid to all_currs
            for i in DB_TDR:  # id, name, cash_type
                if i[-1] == 'Y':
                    all_currs.append([i[0], i[1], CASH_PTYPE_GUID])
                else:
                    all_currs.append([i[0], i[1], NON_CASH_PTYPE_GUID])
            # Add cmp's and cmp_ptype_guids to all_currs
            all_currs.extend([[cmp[0], cmp[1], CMP_PTYPE_GUID] for cmp in DB_CMP])  # cur_id, cur_name, cur_ptype_guid

            # TNDRS ------ >

            # tndrs data filtering (live only strings that was payed with currencies that has pay_rate = 1.0
            tndr_sorted = [[item[0], item[2]] for item in tndr_list if item[-1] in sorted([code[0] for code in all_currs])]

            tndrs = []  # check_id, cur_guid, ptype_guid

            for i in tndr_sorted:
                for ptype in all_currs:
                    if i[-1] == ptype[0]:
                        tndrs.append([i[0], to_guid(str(i[1] + CUR_RATE)), ptype[-1]])

            # ITEMS ------>

            items_with_currs_ptypes = []
            # Add currs and ptypes to items
            for i in item_list:
                for tdr in tndrs:
                    if i[0] == tdr[0]:
                        i.extend([tdr[1], tdr[2]])  # add cur_guid and ptype_guid
                        items_with_currs_ptypes.append(i[1:])  # append item without check_num

            # res: date, item_id, qnt, price, discprice, sales_categ_id, cur_guid, ptype_guid

            # Reformat items_list for using group and count AND ADD SELL_GUID FOR REFUNDS!!!
            items_sorted = [[i[0], to_guid(num=str(i[1])), to_guid(num=str(i[5])), i[7], i[6], '0', i[2], i[3], i[4]]
                            for i in items_with_currs_ptypes]

            # res: date, item_guid, scateg_guid, ptype_guid, cur_guid, refund, qnt, price, discprice
            # print(len(items_sorted))

            # ITEMS REFUND ------------------------------------------>

            for i in items_sorted:
                # actions with refunds
                if i[-1] < 0 or i[-2] < 0:
                    # add modified (ptype, cur == '0' and positive totals) + refund guid
                    items_sorted.append([i[0], i[1], i[2], '0', '0', REFUND_GUID, i[-3], abs(i[-2]), abs(i[-1])])
                    # remove negative refund item
                    items_sorted.remove(i)
                    # remove positive refund item
                    items_sorted.remove([i[0], i[1], i[2], i[3], i[4], i[5], i[-3], abs(i[-2]), abs(i[-1])])

            # res: data, item, scateg, ptype, cur, refund/sell, qnt, price, discprice
            # print(len(items_sorted))

            # ITEMS SELECT BY INI_GROUP -------------------------------------------------------->

            items = []

            if INI_GROUPS == '1':  # by types
                for k, g in groupby(sorted(items_sorted), key=itemgetter(0, 1, 2, 3, 5)):
                    grps = tee(g, 3)
                    items.append([*k, *(sum(v[i] for v in g) for i, g in enumerate(grps, 6))])
                # print(items)  # date, item_guid, scateg_guid, ptype_guid, refund, qnt, price, discprice

            elif INI_GROUPS == '2':
                # INI_GROUP = '1' (by ptypes)
                for k, g in groupby(sorted(items_sorted), key=itemgetter(0, 1, 2, 4, 5)):
                    grps = tee(g, 3)
                    items.append([*k, *(sum(v[i] for v in g) for i, g in enumerate(grps, 6))])
                # print(items)  # date, item_guid, scateg_guid, cur_guid, refund, qnt, price, discprice

            else:  # 3
                # INI_GROUP = '3' (by sells)
                for k, g in groupby(sorted(items_sorted), key=itemgetter(0, 1, 2, 5)):
                    grps = tee(g, 3)
                    items.append([*k, *(sum(v[i] for v in g) for i, g in enumerate(grps, 6))])

                # print(items)  # date, item_guid, scateg_guid, refund, qnt, price, discprice

            return items

        items = get_items(item_list=item, tndr_list=tndr)

        # ITEMS MAIN LOOP ------------------------->

        for i in items:  # date, item_guid, scateg_guid, ptype_guid, cur_guid, refund, qnt, price, discprice
            # Add refunds
            if i[-4] == REFUND_GUID and INI_REFUNDS == '1':  # if refund item and refunds is 'ON' in INI

                date.append(str(i[0]))
                good_guid.append(i[1])
                good_qnt.append(i[-3])
                spec.append(0)
                corr_guid.append(i[-4])

                # sunit
                if INI_SUNITS == '2': sunit_guid.append(i[2])  # by aloha scateg
                else: sunit_guid.append(SUNIT_DEFAULT_GUID)

                # totals
                if INI_TOTALS == '1': good_total.append(i[-1])  # discprice
                else: good_total.append(i[-2])  # price

            elif i[-4] != REFUND_GUID:

                date.append(str(i[0]))
                good_guid.append(i[1])
                good_qnt.append(i[-3])
                spec.append(0)

                # sunits
                if INI_SUNITS == '2': sunit_guid.append(i[2])  # by aloha scateg
                else: sunit_guid.append(SUNIT_DEFAULT_GUID)

                # totals
                if INI_TOTALS == '1': good_total.append(i[-1])  # discprice
                else: good_total.append(i[-2])  # price

                #corrs
                if INI_GROUPS == '1' or INI_GROUPS =='2': corr_guid.append(i[-5])  # ptype, cur
                else: corr_guid.append(SELL_GUID)  # sells (by default)

        # SORT AND REFORMAT VOIDS ----------------------------->

        def get_voids(void_list: list):

            """ Reformat incoming void list """

            cits = sorted([item for item in DB_CIT if item[1] in [categ[0] for categ in DB_CAT]])  # [[item_id, sunit]]

            voids_sorted = []
            for i in void_list:  # check, date, item_id, price, reason_id
                if INI_VOIDS == '1':  # All
                    for cit in cits:  # item_id, sunit
                        if i[2] == cit[0]:
                            i.append(to_guid(num=str(cit[1])))
                            voids_sorted.append([str(i[1]), to_guid(num=str(i[2])), i[-1], to_guid(num=str(i[-2] + RSN_RATE)), 1.0, i[-3]])
                elif INI_VOIDS == '2' and str(i[-1]) in INI_RSN_CODES:
                    for cit in cits:  # item_id, sunit
                        if i[2] == cit[0]:
                            i.append(to_guid(num=str(cit[1])))
                            voids_sorted.append([str(i[1]), to_guid(num=str(i[2])), i[-1], to_guid(num=str(i[-2] + RSN_RATE)), 1.0, i[-3]])
                else:
                    pass

                # date, item_guid, sunit_guid, rsn_guid, qnt, price

                # Summarize
                voids_res = []
                if voids_sorted:
                    for k, g in groupby(sorted(voids_sorted), key=itemgetter(0, 1, 2, 3)):
                        grps = tee(g, 2)
                        voids_res.append([*k, *(sum(v[i] for v in g) for i, g in enumerate(grps, 4))])

                # print(voids)  # res: date, item_guid, sunit_guid, rsn_guid, qnt, price
                return voids_res

        voids = get_voids(void_list=void)

        # VOIDS MAIN LOOP ---------------->

        if voids:  # date, item_guid, sunit_guid, rsn_guid, qnt, price
            for i in voids:
                date.append(i[0])
                good_guid.append(i[1])
                if INI_SUNITS == '1':
                    sunit_guid.append(SUNIT_DEFAULT_GUID)
                else:
                    sunit_guid.append(i[2])
                corr_guid.append(i[3])
                good_qnt.append(i[4])
                good_total.append(5)
                spec.append(0)

    repl_odocs = {
    "UserName": INI_USER,
    "Password": INI_PASS,
    "ProcName": 'ReplODocs',
    "Input": [
        {
            "Head": "222",
            "Original": ['221\\31', '221\\226\\4', '221\\107\\4', '210\\4', '9', '55', '42'],
            "Values": [date, sunit_guid, corr_guid, good_guid, good_qnt, good_total, spec]
        }
    ]
}

    return repl_odocs


def start():

    """ Start program """

    print('Aloha POS to StoreHouse 5 Data Import Utility v 2.01')
    print('Created by Dmitry_R. Support: everycas@gmail.com\n')

    with open(LOG_NAME, 'w') as log_file:
        log_file.write(f'{DT_NOW} -> Start!\n\n')

    sunits = sunits_json()
    ggroups = ggroups_json()
    goods = goods_json()
    corrs = corrs_json()
    shifts = get_period()
    odocs = odocs_json(period=shifts)

    api_request(proc_json=sunits)
    api_request(proc_json=ggroups)
    api_request(proc_json=goods)
    api_request(proc_json=corrs)
    api_request(proc_json=odocs)

    print('\nImport successful!')
    with open(LOG_NAME, 'a') as log_file:
        log_file.write(f'{DT_NOW} -> All requests are successfully done! Stop.\n\n')


start()

