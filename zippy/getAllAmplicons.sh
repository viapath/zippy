sqlite3 /var/local/zippy/zippy.sqlite 'select chrom,start,end,pairid from pairs' | perl -pe 's/\|/\t/g' | sort -k1,1 -k2n,3n > all.bed
