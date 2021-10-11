import requests
import json
import sys, getopt
import pprint
from datetime import datetime, timedelta
iex_date_pattern = '%Y-%m-%d'

# get data from elasticsearch server 
def get_data(input_file, start_date, end_date, symbol):
    url = 'http://localhost:9200/fidelity28_fund/_search?pretty'
    with open(input_file) as f:
        payload = json.load(f)
    payload_json = json.dumps(payload)
    start_datetime = datetime.strptime(start_date, iex_date_pattern)
    new_start_datetime = start_datetime - timedelta(days=49)
    new_start_date = new_start_datetime.strftime(iex_date_pattern)
    payload_json = payload_json % (new_start_date, end_date, symbol)
    headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
    r = requests.post(url, data=payload_json, headers=headers)
    return r.text


# get the command line parameters for the trading policy and the ticker symbol
def get_opt(argv):
    input_file = ''
    symbol = ''
    start_date = ''
    end_date = ''

    try:
        opts, args = getopt.getopt(argv, "hi:s:b:e:")
    except getopt.GetoptError:
        print('backtest_rsis -i <inputfile> -s <symbol> -b <start date> -e <end date>')
        print('example: backtest_rsis.sh -i backtest_rsis.json -s FDEV -b 2020-12-15 -e 2021-05-31')
        sys.exit(-1)

    for opt, arg in opts:
        if opt == '-h':
            print('backtest_rsis -i <inputfile> -s <symbol> -b <start date> -e <end date>')
            print('example: backtest_rsis.sh -i backtest_rsis.json -s FDEV -b 2021-02-01 -e 2021-05-31')
            sys.exit(0)
        elif opt == '-i':
            input_file = arg
        elif opt == '-s':
            symbol = arg
        elif opt == '-b':
            start_date = arg
        elif opt == '-e':
            end_date = arg

    if input_file == '' or start_date == '' or end_date == '' or symbol == '':
        print("Given value is invalid such as no input file, no start, end date or symbol!")
        print('backtest_rsis -i <inputfile> -s <symbol> -b <start date> -e <end date>')
        print('example: backtest_rsis.sh -i backtest_rsis.json -s FDEV -b 2021-02-01 -e 2021-05-31')
        sys.exit(-1)
    print("input_file '%s', start_date '%s', end_Date '%s', symbol '%s'" % (input_file, start_date, end_date, symbol))
    return input_file, start_date, end_date, symbol


# parse the response data and refine the buy/sell signal
def parse_data(resp, start_date):
    result = json.loads(resp)
    if "status" in result:
        print("Return status: %s, error: %s" % (result['status'], result['error']))
        sys.exit(-1)
    aggregations = result['aggregations']
    if aggregations and 'Backtest_RSIs' in aggregations:
        Backtest_RSI = aggregations['Backtest_RSIs']

    transactions = []
    initGain = 0
    initLoss = 0
    wsGain = 0
    wsLoss = 0
    count = 0
    if Backtest_RSI and 'buckets' in Backtest_RSI:
        for bucket in Backtest_RSI['buckets']:
            transaction = {}
            transaction['date'] = bucket['key_as_string']
            transaction['Close'] = bucket['Close']['value']
            transaction['RSISMA14'] = "hold" if 'RSISMA14' not in bucket else ("buy" if bucket['RSISMA14']['value'] < 30 else \
                ("sell" if bucket['RSISMA14']['value'] > 70 else "hold"))
            transaction['RSIEWMA27S'] = "hold" if 'RSIEWMA27S' not in bucket else ("buy" if bucket['RSIEWMA27S']['value'] < 30 else \
                ("sell" if bucket['RSIEWMA27S']['value'] > 70 else "hold"))
            transaction['RSIEWMA27L'] = "hold" if 'RSIEWMA27L' not in bucket else ("buy" if bucket['RSIEWMA27L']['value'] < 30 else \
                ("sell" if bucket['RSIEWMA27L']['value'] > 70 else "hold"))

            count += 1
            if count <= 14:
                initGain += bucket['Gain']['value']
                initLoss += bucket['Loss']['value']
                wsGain = initGain/count
                wsLoss = initLoss/count
            else:
                wsGain = (13 * wsGain + bucket['Gain']['value'])/14
                wsLoss = (13 * wsLoss + bucket['Loss']['value'])/14
                wsRSI = 100 - 100/(1+wsGain/wsLoss)
                transaction['RSISMMA14'] = "buy" if wsRSI < 30 else ("sell" if wsRSI > 70 else "hold")

            if transaction['date'] >= start_date:
                transactions.append(transaction)

    return transactions


def report(transactions, method):
    #pp = pprint.PrettyPrinter(indent=4)
    print('-' * 80)
    print(method)
    #pp.pprint(transactions)

    profit = 0.0;
    num_of_buy = 0
    num_of_sell = 0
    buy_price = 0;
    win = 0
    lose = 0
    max_buy_price = 0
    hold = False
    for transaction in transactions:
        if transaction[method] == 'buy' and not hold:
           num_of_buy += 1
           buy_price = transaction['Close']
           profit -= transaction['Close']
           max_buy_price = transaction['Close'] if max_buy_price < transaction['Close'] else max_buy_price
           hold = True
        elif transaction[method] == 'sell' and hold:
           profit += transaction['Close']
           if transaction['Close'] > buy_price:
               win += 1
           else:
               lose += 1
           buy_price = 0
           num_of_sell += 1
           hold = False
        else:
            transaction[method] == 'hold'

    if buy_price > 0:
        profit += transactions[-1]['Close']
        if transaction['Close'] > buy_price:
            win += 1
        else:
            lose += 1

    print('number of buy:      %8d' % (num_of_buy))
    print('number of sell:     %8d' % (num_of_sell))
    print('number of win:      %8d' % (win))
    print('number of lose:     %8d' % (lose))
    print('total profit:       %8.2f' % (profit))
    if num_of_buy > 0:
        print('profit/transaction: %8.2f' % (profit/num_of_buy))
    print('maximum buy price:  %8.2f' % max_buy_price)
    if max_buy_price > 0:
        print('profit percent:     %8.2f%%' % (profit*100/max_buy_price))
    print('-' * 80)
    print()


def main(argv):
    input_file, start_date, end_date, symbol = get_opt(argv)
    resp = get_data(input_file, start_date, end_date, symbol)
    transactions = parse_data(resp, start_date)
    report(transactions, 'RSISMA14')
    report(transactions, 'RSIEWMA27S')
    report(transactions, 'RSISMMA14')


if __name__ == '__main__':
    main(sys.argv[1:])
