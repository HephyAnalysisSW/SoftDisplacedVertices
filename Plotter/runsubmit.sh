for year in 17 18 22Pre 22Post 23Pre 23Post
do
    /groups/hephy/cms/ang.li/Tools/scripts/submit_el8 jobs_data${year}.sh --title=${year}data --nCPUs=4
    #/groups/hephy/cms/ang.li/Tools/scripts/submit_el8 jobs_bkg${year}.sh --title=${year}bkg --nCPUs=4
done
for year in 17 18 22Pre 22Post 23Pre 23Post
do
    #/groups/hephy/cms/ang.li/Tools/scripts/submit_el8 jobs_data${year}.sh --title=${year}data --nCPUs=4
    /groups/hephy/cms/ang.li/Tools/scripts/submit_el8 jobs_bkg${year}.sh --title=${year}bkg --nCPUs=4
done

/groups/hephy/cms/ang.li/Tools/scripts/submit_el8 jobs_sig18.sh  --title=18sig
