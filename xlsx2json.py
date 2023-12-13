## https://amis.afa.gov.tw/fruit/FruitProdDayTransInfo.aspx

from pandas import read_excel  
from re import compile as newRE
from json import dumps as jsdump

df = read_excel("db/fruits.xls")

print(df.head())
print("=============================================================================================")

checker = newRE("^\d+/\d+/\d+$");
doc={};
cs={};
for row in df.values.tolist()[4:] :
    if not checker.match(row[0]) : continue
    key = row[1].split()[0]+"-"+row[2].split()[1]
    if row[0] not in doc :
        doc[row[0]] = {}
    cs[key+"-P"]=True
    doc[row[0]][key+"-P"]=row[6]
    cs[key+"-V"]=True
    doc[row[0]][key+"-V"]=row[8]

lastV={};
cs=sorted(cs.keys())
out={"Date":[]}
xs = sorted(doc.keys())
for d in xs :
    dt=d.split("/");
    out["Date"].append(str(1911+int(dt[0]))+"-"+dt[1]+"-"+dt[2]);
    for k in cs :
        if k not in out : out[k]=[];
        if k in doc[d] :
            lastV[k] = doc[d][k];
            out[k].append( doc[d][k] )
        else :
            out[k].append( lastV[k] if k in lastV else 0 )

with open("docs/db/fruit.json","w",encoding="utf8") as fo :
    fo.write(jsdump(out,ensure_ascii=False))
