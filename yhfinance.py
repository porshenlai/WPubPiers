from pandas import read_csv
from time import time
from os import makedirs
from sys import argv

def fetchYF( sid, since=None, until=None ) :
    if not until:
        until = time()
    until=86400*(until//86400)

    if since:
        since=86400*(since//86400)
    else :
        since=until - 86400*365

    return read_csv( "https://query1.finance.yahoo.com/v7/finance/download/%s?period1=%d&period2=%d&interval=1d&events=history&includeAdjustedClose=true" % (sid, since, until) );

makedirs("docs/db/",exist_ok=True)
for sid in argv[1:] :
	df=time()
	df=fetchYF( sid, since=df-86400*int(365.25*5), until=df )
	df.to_json("docs/db/%s.json" % sid);
	print("docs/db/%s.json updated." % sid)
