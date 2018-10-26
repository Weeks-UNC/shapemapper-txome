import sys, os

#ids = """
#ENSMUST00000192833.1
#ENSMUST00000157463.1
#ENSMUST00000083103.1
#ENSMUST00000153941.7
#ENSMUST00000175032.2
#ENSMUST00000174924.2
#ENSMUST00000185587.1
#ENSMUST00000090043.6
#ENSMUST00000172812.2
#""".strip().split()

#fas = ["Mus_musculus.GRCm38.cdna.all.fa", 
#       "Mus_musculus.GRCm38.ncrna.fa"]

ids = open("top_cds_ids","rU").read().strip().split()

fas = ["Mus_musculus.GRCm38.cds.all.fa"]

out = open("top_transcripts_cds.fa", "w")

seqs = {ID:"" for ID in ids}
for fa in fas:
    f = open(fa, "rU")
    ID = ""
    seq = ""
    for line in f:
        if line[0] == '>':
            if ID != "":
                # store previous sequence
                seqs[ID] = seq
            seq = ""
            ID = line[1:].split()[0]
            if ID not in ids:
                ID = "" # skip transcripts not selected
        else:
            seq += line.strip()
#print(len(seqs["ENSMUST00000157463.1"]))
#assert (len(seqs["ENSMUST00000157463.1"]) == 271)

for ID in seqs:
    out.write(">{}\n{}\n".format(ID, seqs[ID]))
