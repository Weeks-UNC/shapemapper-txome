import sys, os


plus_frag_length = float(sys.argv[1])
minus_frag_length = float(sys.argv[2])
plus_abund = open(sys.argv[3], "rU")
minus_abund = open(sys.argv[4], "rU")
min_mean_depth = int(sys.argv[5])
o = open(sys.argv[6], "w")

def load_depths(abund, frag_length):
    depths = {}
    abund.readline()
    for line in abund:
        s = line.strip().split()
        if len(s) < 5:
            continue
        ID = s[0]
        length = int(s[1])
        est_counts = float(s[3])
        est_mean_depth = frag_length * est_counts / length
        depths[ID] = est_mean_depth
        print str(est_mean_depth)
    return depths

plus_depths = load_depths(plus_abund, plus_frag_length)
minus_depths = load_depths(minus_abund, minus_frag_length)

selected = []
for ID in plus_depths:
    if plus_depths[ID] >= min_mean_depth and minus_depths[ID] >= min_mean_depth:
        selected.append(ID)
IDs = selected

# TODO: eliminate overlapping CDS IDs?    
    
for ID in IDs:
    o.write("{}\n".format(ID))
