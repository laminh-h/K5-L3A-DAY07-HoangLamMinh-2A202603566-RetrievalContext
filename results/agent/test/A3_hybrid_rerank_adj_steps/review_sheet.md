# Review sheet - A3_hybrid_rerank_adj_steps / test

## q16 (direct) - status `answered`

**Q:** What was the Vietnam Manufacturing PMI in September 2017?  
**Expected:** 53.3, up from 51.8 in August.  
**Gold:** ts-2017-12 p17: "rose to 53.3 in September from 51.8 in August"  
**Auto:** {'context_evidence': True, 'first_search_hit_at_3': True, 'cited_evidence_chunk': False}  
**Searches (2):** ['Manufacturing PMI September 2017', 'A:ts-2017-12:p017:c05']  
**Answer:** The headline Vietnam Manufacturing Purchasing Managers' Index (PMI) rose to 53.3 in September 2017.  

> **[A:ts-2017-12:p017:c05]** ts-2017-12 p17: ction expanded by 8.6 percent (y/y) during the first ten months of 2017- much higher than the same period last year (7.3 percent). Strong performance in manufacturing sector, which grew 13.6 percent, compensated the decline in mining sector which is down 7.4 percent y/y. Manufacturing output recovered from one-off factors such as the Samsung recall and a decline in steel production by Formosa. The headline Vietnam Manufacturing Purchasing Managers' Index (PMI) rose to 53.3 in September from 51.8

## q17 (paraphrase) - status `answered`

**Q:** In the 2016 customs survey, what share of declarations went through the green channel?  
**Expected:** 59.8 percent of the total number of declarations.  
**Gold:** ts-2018-06 p46: "the green channel accounts for 59.8 percent of the total number of declarations"  
**Auto:** {'context_evidence': True, 'first_search_hit_at_3': True, 'cited_evidence_chunk': True}  
**Searches (2):** ['customs survey green channel share 2016', 'A:ts-2018-06:p046:c00']  
**Answer:** In the 2016 survey of Vietnam Customs, the green channel accounted for 59.8 percent of the total number of declarations.  

> **[A:ts-2018-06:p046:c00]** ts-2018-06 p46: 27. Customs is responsible for the last intervention for goods clearance at border. However, compliance costs depend not only on Customs, but also on specialized agencies before and at the border. Figure 14. Goods Cleared by Type of Channel Source: Vietnam Customs (2016). 28. A survey of Vietnam Customs (2016) using 9.48 million customs declarations reveals (Figure 14) that the green channel accounts for 59.8 percent of the total number of declarations. Too many changeable legal documents guidin

## q18 (condition_exception) - status `answered`

**Q:** How old is Vietnam's active trucking fleet on average, compared with countries such as Australia or Japan?  
**Expected:** 17 years on average, versus 14 years in Australia and 9 years in Canada and Japan.  
**Gold:** ts-2018-06 p50: "active trucking fleet is 17 years, much greater than 14 years in Australia, 9 years in Canada and Japan"  
**Auto:** {'context_evidence': True, 'first_search_hit_at_3': True, 'cited_evidence_chunk': True}  
**Searches (2):** ['trucking fleet average age Australia Japan', 'A:ts-2018-06:p050:c02']  
**Answer:** The average age of Vietnam's active trucking fleet is 17 years, which is much greater than 14 years in Australia and 9 years in Japan (as well as 9 years in Canada, 8 years in the U.K., and 6-6.5 years in the U.S. and France).  

> **[A:ts-2018-06:p050:c02]** ts-2018-06 p50: argest asset-based LSP , faces a significant efficiency gap: about 35 percent of truck miles are empty according to a World Bank study in 2010, and the average age of Vietnam's active trucking fleet is 17 years, much greater than 14 years in Australia, 9 years in Canada and Japan, 8 years in the U.K., and 6-6.5 years in U.S. and France. Similar is true for inland waterway sector: the average barge size in Vietnam is at 100 deadweight tons, minuscule compared to 2,400 tons in Western Europe with 

## q19 (metadata_filter) - status `answered`

**Q:** What was Vietnam's overall fiscal deficit in 2017 as a percentage of GDP?  
**User filter:** {'edition': '2018-06'}  
**Expected:** An estimated 4.5 percent of GDP in 2017 (from 4.8 percent in 2016), IMF GFS definition.  
**Gold:** ts-2018-06 p28: "an estimated 4.5 percent of GDP in 2017 from 4.8 percent in 2016"  
**Auto:** {'context_evidence': True, 'first_search_hit_at_3': True, 'cited_evidence_chunk': True}  
**Searches (1):** ['fiscal deficit 2017 GDP']  
**Answer:** Vietnam's overall fiscal deficit narrowed to an estimated 4.5 percent of GDP in 2017 (IMF GFS definition).  

> **[A:ts-2018-06:p028:c03]** ts-2018-06 p28:  MOF , World Bank and IMF . Thanks to a continued adjustment in the fiscal position, public debt stabilized in 2017 22. Vietnam's fiscal stance improved further in 2017. The overall fiscal deficit is estimated to have narrowed to an estimated 4.5 percent of GDP in 2017 from 4.8 percent in 2016 and 5.5 percent in 2015 (IMF GFS definition) (figure 27). Preliminary figures show that total revenues remained at 23.6 percent of GDP in 2017 - at about the level reported in 2015 and 2016, supported by a

## q20 (metadata_filter) - status `answered`

**Q:** What real GDP growth rate does the World Bank project for Vietnam in 2018?  
**User filter:** {'edition': '2018-06'}  
**Expected:** 6.8 percent in 2018 (revised up from 6.5 percent), then 6.6 percent in 2019 and 6.5 percent in 2020.  
**Gold:** ts-2018-06 p31: "real GDP now projected to expand by 6.8 percent in 2018"  
**Auto:** {'context_evidence': False, 'first_search_hit_at_3': False, 'cited_evidence_chunk': False}  
**Searches (1):** ['real GDP growth rate project 2018 Vietnam June 2018']  
**Answer:** The World Bank projects real GDP to expand by 6.8 percent in 2018.  

> **[A:ts-2018-06:p010:c00]** ts-2018-06 p10: Medium-term outlook, risks, and policy implications Vietnam's medium-term outlook has improved further since the last Taking Stock release in December 2017. Real GDP is now projected to expand by 6.8 percent in 2018 (up from 6.5 percent in our previous projection) before moderating to 6.6 percent in 2019 and 6.5 percent in 2020 due to the envisaged cyclical moderation of global demand. Despite reduced slack in the economy, we expect inflation to remain around the 4 percent government target, pre

## u03 (unanswerable) - status `abstain`

**Q:** What regional minimum wage did Vietnam set for 2018?  
**Expected:** abstain - Reports describe average nominal/real wage growth, not the statutory minimum wage.  
**Searches (4):** ['minimum wage 2018 regional Vietnam', 'regional minimum wage 2018', 'minimum wage', 'minimum wage 2018']  
**Answer:** The provided World Bank reports ("Taking Stock" December 2017 and June 2018) do not contain information regarding the specific regional minimum wage set by Vietnam for 2018.  

## u04 (unanswerable) - status `abstain`

**Q:** By what percentage did Vietnam raise the retail electricity tariff in 2017?  
**Expected:** abstain - 'Electricity' only appears in Doing Business 'Getting Electricity' reform text; no retail tariff change is reported.  
**Searches (4):** ['retail electricity tariff 2017 percentage Vietnam', 'electricity tariff 2017 percent', 'retail electricity tariff', 'electricity tariff 2017']  
**Answer:** The provided World Bank reports ("Taking Stock" December 2017 and June 2018) do not contain information on the percentage by which Vietnam raised the retail electricity tariff in 2017.  

