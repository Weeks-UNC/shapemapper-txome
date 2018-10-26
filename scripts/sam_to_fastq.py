import sys, os

#IDs = """
#ENSMUST00000192833.1
#ENSMUST00000157463.1
#ENSMUST00000083103.1
#ENSMUST00000153941.7
#ENSMUST00000174924.2
#ENSMUST00000185587.1
#ENSMUST00000090043.6
#ENSMUST00000172812.2
#""".strip().split()

idfile = open(sys.argv[1], "rU")
infile = open(sys.argv[2], "rU")
outR1 = sys.argv[3]
outR2 = sys.argv[4]

IDs = idfile.read().strip().split()

folder, outname = os.path.split(outR1)
#os.makedirs(folder, exist_ok=True)
folder, outname = os.path.split(outR2)
#os.makedirs(folder, exist_ok=True)

o1 = open(outR1, "w")
o2 = open(outR2, "w")

i=1
for line in infile:
    if line[0] == '@':
        continue
    if i % 10000 == 0:
        sys.stdout.write("{}\n".format(i))
    i += 1
    s = line.strip().split('\t')
    cluster_id = s[0]
    flags = int(s[1])
    # R1:64 R2:128
    r = 1
    if flags & 128 != 0:
        r = 2
    target_id = s[2]
    read = s[9]
    qual = s[10]
    if target_id in IDs:
        if r == 1:
            o1.write("@{}\n{}\n+\n{}\n".format(cluster_id, read, qual))
        else:
            o2.write("@{}\n{}\n+\n{}\n".format(cluster_id, read, qual))
    
    
