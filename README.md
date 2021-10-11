# Backtest_RSI
Materials for the article "Wow! Backtest RSI Crossover Strategy in Elasticsearch" in Medium
(https://wtwong316.medium.com/wow-backtest-rsi-crossover-strategy-in-elasticsearch-1cdf837a72a1)

The following steps have been tested with Elasticsearch Server v7.10.1

1. Create an index, fidelity28_fund and the corresponding data are populated. The data for the index, fidelity28_fund, is coming from IEX (Investors Exchange) with the 28 Fidelity commission-free ETFs selected for demo purpose. The time range picked is between 2020-12-15 and 2021-05-31.

./fidelity28_index.sh

2. Assume you have installed python 3.7, run the following command to go to virtual environment and prepare the python packages needed.

source venv/bin/activate

pip install -r requirements.txt

3. After the indices are created and the data are populated, You can try different ticker symbol such as FDEV, FMAT, FTEC, FHLC, FENY, FSTA, FDIS, FQAL, FDLO, FDMO and FUTY to backtest the RSI trading strategy. A report will be shown for the statistical data.

./backtest_rsi.sh FDEV


