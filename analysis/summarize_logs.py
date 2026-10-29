import re,glob,sys,json
arch=['CNN','GoogLeNet','MobileNetV2','ResNet18']
out={}
for f in sorted(glob.glob(sys.argv[1]+'/**/*.*',recursive=True)):
    t=open(f,encoding='utf-8',errors='ignore').read()
    name=f.split('/')[-1].rsplit('.',1)[0]
    acc=[float(a)*100 for a in re.findall(r'Averaged Test Accuracy: ([\d.]+)',t)]
    std=[float(a)*100 for a in re.findall(r'Std Test Accuracy: ([\d.]+)',t)]
    tm=[float(x) for x in re.findall(r'^-{20,}[^\n]*?([\d.]+)\s*$',t,re.M)]
    per=[]
    for b in t.split('Evaluate heterogeneous models')[1:]:
        cs=re.findall(r'Client (\d+): Acc: ([\d.]+)',b)
        if len(cs)<20: continue
        per.append([sum(float(a) for c,a in cs if int(c)%4==k)/5*100 for k in range(4)])
    i=acc.index(max(acc))
    print(f"{name:22} evals={len(acc):2d} best={max(acc):6.2f}@r{i:<2d} last={acc[-1]:6.2f} std@best={std[i]:5.2f} min/rnd={sum(tm)/max(len(tm),1)/60:5.1f} {'DONE' if 'All done' in t else ('CRASH' if 'Traceback' in t else '')}")
    print('   curve:',' '.join('%.1f'%a for a in acc))
    if per: print('   arch first/best/last:',' | '.join('%s %.1f/%.1f/%.1f'%(arch[k],per[0][k],per[min(i,len(per)-1)][k],per[-1][k]) for k in range(4)))
    out[name]=dict(acc=acc,std=std,per=per,min_per_round=sum(tm)/max(len(tm),1)/60,done='All done' in t)
json.dump(out,open(sys.argv[2],'w'))
