#!/usr/bin/env python3
"""Validate manually discovered public founder routes from authoritative pages.

This queue is intentionally separate from search-result extraction. Every row
must carry an exact source URL, an independent identity URL, and a public
email copied from the cited page. No address is generated here.
"""
from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import signal
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from engine.real_retrieval import fetch_source

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "verified100"

SEEDS = [
    {"name":"Vijayraj Parmar","company":"Sanjay Chemicals (India) Pvt. Ltd.","role":"Founder & Chairman","industry":"Chemicals","email":"vijayraj@sanjaychemindia.com","contact_url":"https://www.sanjaychemindia.com/team.php","identity_url":"https://sanjaychemindia.com/mission.php/js/wow.min.js"},
    {"name":"Dilip Parmar","company":"Sanjay Chemicals (India) Pvt. Ltd.","role":"Managing Director","industry":"Chemicals","email":"dilip@sanjaychemindia.com","contact_url":"https://www.sanjaychemindia.com/team.php","identity_url":"https://www.indiafilings.com/search/sanjay-chemicals-india-private-limited-cin-U51434MH2000PTC129290"},
    {"name":"Manoj Parmar","company":"Sanjay Chemicals (India) Pvt. Ltd.","role":"Director","industry":"Chemicals / Pharma Supply","email":"manoj@sanjaychemindia.com","contact_url":"https://www.sanjaychemindia.com/team.php","identity_url":"https://kandlacustoms.gov.in/wp-content/uploads/2015/10/04-2014-15-Sanjay-Chem.pdf"},
    {"name":"Sanjay Parmar","company":"Sanjay Chemicals (India) Pvt. Ltd.","role":"Director","industry":"Chemicals / Exports","email":"sanjay@sanjaychemindia.com","contact_url":"https://www.sanjaychemindia.com/team.php","identity_url":"https://kandlacustoms.gov.in/wp-content/uploads/2015/10/04-2014-15-Sanjay-Chem.pdf"},
    {"name":"Deepak Khandelwal","company":"Easy Logistic Solutions","role":"Founder & CEO","industry":"Logistics / Warehousing","email":"deepak@easylogistic.co.in","contact_url":"https://www.easylogistic.co.in/","identity_url":"https://www.easylogistic.co.in/"},
    {"name":"Mohan Krishna Challaturu","company":"IndMALL Automation / Challaturu Engineering & Automation","role":"Founder & Director","industry":"Industrial Automation","email":"mohan@challaturu.com","contact_url":"https://indmall.co.in/about-us/","identity_url":"https://www.indmall.in/about-us/"},
    {"name":"Ayush Tiwary","company":"KRISEVA AI","role":"Founder","industry":"AI / Procurement Technology","email":"ayush@kriseva.in","contact_url":"https://www.kriseva.in/contact/","identity_url":"https://in.linkedin.com/in/ayushtiwary7"},
    {"name":"Garvit Jain","company":"Vardhan AI","role":"Founder","industry":"AI / Business Automation","email":"garvit@vardhanai.com","contact_url":"https://vardhanai.com/about","identity_url":"https://vardhanai.com/"},
    {"name":"Jay Singh","company":"Corino AI","role":"Founder","industry":"AI / Productivity Software","email":"jay.singh@corino.ai","contact_url":"https://corino.ai/about","identity_url":"https://corino.ai/"},
    {"name":"Sonia Uppal","company":"Curioso Technologies","role":"Co-Founder","industry":"AI / Enterprise Software","email":"sonia.uppal@curiosobyte.com","contact_url":"https://curiosobyte.com/","identity_url":"https://www.indiafilings.com/search/curioso-technologies-private-limited-cin-U72900KA2016PTC097044"},
    {"name":"Ahamed Shafeek","company":"Z3Connect / Z2Learn","role":"Founder & CEO","industry":"AI / B2B Software","email":"ahamed@ahamedshafeek.com","contact_url":"https://ahamedshafeek.me/","identity_url":"https://ahamedshafeek.me/"},
    {"name":"Raghav Bahl","company":"Quint Digital / Network18","role":"Founder / Co-Founder","industry":"Media Technology / Digital Business","email":"raghav.bahl@thequint.com","contact_url":"https://www.sebi.gov.in/sebi_data/commondocs/jan-2020/lof%20Gaurav%20Mercantiles%20Limited_p.PDF","identity_url":"https://www.thequint.com/author/51/raghav-bahl"},
    {"name":"R. C. Juneja","company":"Mankind Pharma","role":"Founder, Chairman & Managing Director","industry":"Pharma","email":"rcjuneja@mankindpharma.com","contact_url":"https://www.fopeindia.com/office_bearers/details/51","identity_url":"https://www.cipi.co.in/office_bearears"},
    {"name":"Kiran Mazumdar-Shaw","company":"Biocon","role":"Founder / Executive Chairperson","industry":"Pharma / Biotechnology","email":"kiran.mazumdar@biocon.com","contact_url":"https://www.biocon.com/docs/Initmation_Change_in_policy_signed-20230214.pdf","identity_url":"https://www.biocon.com/about-us/board-of-directors-biocon/kiran-mazumdar-shaw-biocon/"},
    {"name":"Dilip Shanghvi","company":"Sun Pharmaceutical Industries","role":"Founder & Executive Chairman","industry":"Pharma","email":"dilip.shanghvi@sunpharma.com","contact_url":"https://archives.nseindia.com/corporate/SUNPHARMA_20042021111153_Sunpharma.pdf","identity_url":"https://sunpharma.com/board-of-directors/"},
    {"name":"Sushil Kumar","company":"Altahar / DWA Herbals","role":"Founder / CEO","industry":"Consumer Health / Manufacturing","email":"sushil.kumar@dwaherbals.com","contact_url":"https://altahar.com/pages/founder-dr-sushil-kumar","identity_url":"https://in.linkedin.com/in/sushil-kumar-5495a712"},
    {"name":"Saket Saraf","company":"Independent Software Business","role":"Founder / Product Builder","industry":"Software","email":"saket.saraf@gmail.com","contact_url":"http://saketsaraf.com/saketsaraf/contact-me","identity_url":"https://in.linkedin.com/in/saketksaraf"},
    {"name":"Ashutosh Shinde","company":"The Indian Export Company","role":"Founder","industry":"Exports / Agricultural Supply","email":"ashutosh@theindianexportcompany.com","contact_url":"https://theindianexportcompany.com/about/","identity_url":"https://in.linkedin.com/in/ashutosh-shinde-"},
    {"name":"Sunil Jugal Kishore Shah","company":"Safe Reach Logistics","role":"Founder & Managing Director","industry":"Logistics / Warehousing","email":"sunil1977shah@gmail.com","contact_url":"https://safereach.in/about/management-team/","identity_url":"https://www.indiafilings.com/search/safe-reach-logistics-private-limited-cin-U63030KA2022PTC161738"},
    {"name":"Vinay Avanchi","company":"IndustriConnect Technologies Pvt. Ltd.","role":"Founder & Director","industry":"Industrial Automation / Engineering","email":"vinay.avanchi@industri-connect.com","contact_url":"https://industri-connect.com/our-team.html","identity_url":"https://industri-connect.com/images/Brochure_Introduction%20to%20Industrial%20Automation.pdf"},
    {"name":"Omkar Pandharkame","company":"BHyve / Supervity AI","role":"Founder & former CEO / Chief Strategy Officer","industry":"AI / B2B SaaS","email":"omkar@supervity.ai","contact_url":"https://www.stackforce.co/talent/omkar-pandharkame-co-founder-69d5e5c726285b1c1ae95df8","identity_url":"https://www.hse.ru/en/ma/socpsy/news/533594853.html"},
    {"name":"Dr. Sowmini Sunkara","company":"Agrighar Services Pvt. Ltd.","role":"Founder","industry":"Agritech / Foodtech / Rural Supply Chains","email":"sowmini@agrighar.com","contact_url":"https://www.manage.gov.in/managecia/ASCIEF%2829.05.2025%29.pdf","identity_url":"https://www.indiafilings.com/search/agrighar-services-private-limited-cin-U01100TG2019PTC137109"},
    {"name":"Anuj Singhai","company":"Sajaivico India Private Limited","role":"Founder","industry":"Agritech / Food Manufacturing","email":"anujsinghai1989@gmail.com","contact_url":"https://www.manage.gov.in/managecia/ASCIEF%2829.05.2025%29.pdf","identity_url":"https://www.ynos.in/startup/sajaivico-389337"},
    {"name":"Prasad Kulkarni","company":"Adrise India Pvt. Ltd. / Vande Kisan","role":"Founder & Business Head","industry":"AI / Agritech / Farmer Platforms","email":"prasad@adriseindia.com","contact_url":"https://www.manage.gov.in/managecia/%28S%28oryvjsgerk2zl5d1ky1rzcvs%29%29/ASCIEF%2829.05.2025%29.pdf","identity_url":"https://www.agriculturetoday.in/at-admin/magazine-pdf/magazine-november-2022.pdf"},
    {"name":"Shivaraj Gowda","company":"Quepreon Biologicals Pvt. Ltd.","role":"Founder & CEO","industry":"Pharma / Biotechnology","email":"shivraj@quepreon.com","contact_url":"https://quepreon.com/landing-page/","identity_url":"https://www.indiafilings.com/search/quepreon-biologicals-private-limited-cin-U33111KA2011PTC056730"},
    {"name":"Mitul Patel","company":"Apollo Inffratech Pvt. Ltd.","role":"Founder / Managing Director","industry":"Manufacturing / Construction Equipment","email":"mitul.patel@apolloinfratech.com","contact_url":"https://www.sundram.com/pdf/SFLStatutoryRegistersFY24.pdf","identity_url":"https://www.apolloinffratech.com/promoters"},
    {"name":"Rajeev Sharma","company":"Sahyog Logistics Solutions Pvt. Ltd.","role":"Founder & Managing Director","industry":"Logistics / Freight Forwarding","email":"raj@sahyogfreight.com","contact_url":"https://sahyogfreight.com/management.php","identity_url":"https://gttcindia.com/executive-members/"},
    {"name":"Srikanta Khatua","company":"Odipak Solution","role":"Founder & Director","industry":"Flexible Packaging","email":"srikanta.khatua@odipaksolution.com","contact_url":"https://assets.zyrosite.com/mjEPJZ4X5EcKK1rQ/odipak-solution---brochure-5th-may-2025_1-mnl436Je8ysvPnQo.pdf","identity_url":"https://odipaksolution.com/about-us"},
    {"name":"Pritish Sahoo","company":"Relyon Packs / Odipak Solution","role":"Founder & Director","industry":"Flexible Packaging","email":"pritish.sahoo@odipaksolution.com","contact_url":"https://assets.zyrosite.com/mjEPJZ4X5EcKK1rQ/odipak-solution---brochure-5th-may-2025_1-mnl436Je8ysvPnQo.pdf","identity_url":"https://piceapp.com/gst-number-search/ms-relyon-packs-21AVRPS6109C1ZN/"},
    {"name":"Rachna Jaiswal","company":"AKJ Industries Pvt. Ltd.","role":"Co-Founder & Director","industry":"Leather Manufacturing / Exports","email":"rachna@akjintl.com","contact_url":"https://rachnajaiswal.com/","identity_url":"https://www.quickcompany.in/directors/07055325-rachna-jaiswal"},
    {"name":"Vijay Zalera","company":"Ajanta Steel Products / Ajanta Marketing","role":"Founder & Chairman","industry":"Manufacturing / Stationery Exports","email":"ajantamkt@gmail.com","contact_url":"https://ajantamkt.in/ceo-company/","identity_url":"https://in.linkedin.com/in/zalera-vijay-511aaaa7"},
    {"name":"K. S. Thomas","company":"Kottackal Industries","role":"Founder / Proprietor","industry":"Manufacturing / Electrical Components / Packaging","email":"kottackalthomas@gmail.com","contact_url":"https://www.kotsun.co.in/about-us.htm","identity_url":"https://www.exportersindia.com/kottackal-industries/about-us.htm"},
    {"name":"Gautam Biswas","company":"SNG Technologies","role":"Founder & Owner / General Manager","industry":"Agricultural Machinery / Food Processing Equipment","email":"gautamsmail2380@gmail.com","contact_url":"https://www.sngtechnologies.co.in/about-the-founder","identity_url":"https://www.tradeindia.com/sng-technologies-11032421/"},
    {"name":"Rashmi Ranjan Mohanty","company":"Advent Chembio Pvt. Ltd.","role":"Co-Founder & Director-Technical","industry":"Chemicals / Pharma Manufacturing","email":"rashmi.mohanty@adventchembio.com","contact_url":"https://www.actrec.gov.in/sites/default/files/latest_events/ACTREC_TMC%20Conclave_Abstract_ADVENT.pdf","identity_url":"https://www.adventchembio.com/about"},
    {"name":"Rajat Vardhan","company":"AgroNxt Services Pvt. Ltd.","role":"Co-Founder & CEO","industry":"AI / Agritech / Industrial Diagnostics","email":"rajat@agronxt.com","contact_url":"https://psa.gov.in/stcluster-dashboard/downloadpdf.php?id=agritech2024","identity_url":"https://indiaspora.org/entrepreneurs-leader/rajat-vardhan/"},
    {"name":"Hemalatha Annamalai","company":"Ampere Vehicles / Green Collar Agritech","role":"Founder & Former CEO","industry":"Electric Vehicle Manufacturing / Agritech","email":"srbhema@gmail.com","contact_url":"https://www.msme.gov.in/sites/default/files/FLOCompendiumof100SucessStoriesofWomeninMSME.pdf","identity_url":"https://ampere-electric.com/about"},
    {"name":"Gayatri Varun","company":"Green Hermitage","role":"Founder & CEO","industry":"Sustainable Manufacturing / Plant-Based Materials","email":"gayatri.varun@greenhermitage.com","contact_url":"https://www.aicnalanda.com/startup_profiles/HDFC_Parivartan_Profile.pdf","identity_url":"https://greenhermitage.com/pages/people"},
    {"name":"Sunil Narwal","company":"Krama / Mavis Communication Services Pvt. Ltd.","role":"Founder & CEO","industry":"AI / Manufacturing Intelligence / Industrial Automation","email":"sunil@krama.ai","contact_url":"https://krama.ai/about.html","identity_url":"https://www.tofler.in/mavis-communication-services-private-limited/company/U74999HR2017PTC067915"},
    {"name":"Sumit Chhabra","company":"Asia Sourcing India","role":"Founder & CEO","industry":"Manufacturing Sourcing / Exports / Quality Control","email":"sumit@asiasourcingindia.com","contact_url":"https://sourcingindia.org/","identity_url":"https://asiasourcing.co.in/"},
    {"name":"Kishan Agola","company":"Pavandeal Homecare Pvt. Ltd.","role":"Founder & CEO","industry":"Manufacturing / Fasteners / Exports","email":"kishanagola@pavandeal.com","contact_url":"https://www.pavandeal.com/contact","identity_url":"https://www.tradeindia.com/pavandeal-homecare-private-limited-159949763/"},
    {"name":"Chhaya Agola","company":"Pavandeal Homecare Pvt. Ltd.","role":"Co-Founder","industry":"Manufacturing / Fasteners / Exports","email":"chhayaagola@pavandeal.com","contact_url":"https://www.pavandeal.com/contact","identity_url":"https://www.linkedin.com/company/pavandeal-homecare-pvt-ltd"},
    {"name":"P. Jesudas","company":"Alpha Packaging","role":"Founder / Managing Director","industry":"Packaging / Industrial Logistics","email":"jesu@alphapackaging.in","contact_url":"https://alphapackaging.in/founder/","identity_url":"https://www.tradeindia.com/alpha-packaging-1405031/"},
    {"name":"Dinesh Paranthagan","company":"Hackup Technology Pvt. Ltd.","role":"Founder & CEO","industry":"AI / Cybersecurity / B2B Technology","email":"dinesh@hackuptechnology.com","contact_url":"https://www.drngpasc.ac.in/pdf/profile/commerce_it/dinesh.pdf","identity_url":"https://www.hackuptechnology.com/become-a-certified-ethical-hacker-ceh-with-hackup-technology-coimbatores-leading-cyber-security-hub/"},
    {"name":"Kalpesh Shah","company":"Rushabh Industries","role":"Founder & Owner","industry":"Pharma Packaging / Manufacturing / Exports","email":"rushabh_ppcaps@yahoo.co.in","contact_url":"https://www.rushabhcaps.com/about-us/team-details","identity_url":"https://www.rushabhcaps.com/about-us"},
    {"name":"Divya Jain","company":"Safeducate Learning Pvt. Ltd.","role":"Founder & CEO","industry":"Logistics / Supply Chain Education / Workforce Development","email":"divya.jain@safeducate.com","contact_url":"https://www.safeducate.com/assets/pdf/Safeducate-Times-January.pdf","identity_url":"https://safeducateonline.in/about-us/"},
    {"name":"Eela Dubey","company":"EduFund / Helena Edtech Pvt. Ltd.","role":"Co-Founder & CEO","industry":"Fintech / Education Finance","email":"eela@edufund.in","contact_url":"https://ciiwrevents.in/pdf/New%20Membership%20Applicaitons_for_Tabling.pdf","identity_url":"https://www.edufund.in/about-us/"},
    {"name":"Pranav Bhalara","company":"Balaji Multiflex Pvt. Ltd. / Pouch N Pack","role":"Founder / Executive Director","industry":"Flexible Packaging / Manufacturing","email":"pbhalara@balajimultiflex.com","contact_url":"https://www.bseindia.com/xml-data/corpfiling/AttachHis/bb199383-6cdc-4aa4-b901-6d316d4f460c.pdf","identity_url":"https://www.careratings.com/upload/CompanyFiles/PR/202401140142_Balaji_MultiFlex_Private_Limited.pdf"},
    {"name":"Nilesh Jariwala","company":"Neelkamal Industries","role":"Founder & CEO","industry":"Textile Manufacturing / Exports","email":"neelkamalind@gmail.com","contact_url":"https://www.exportersindia.com/neelkamal-industries-surat/neelkamal-industries.pdf","identity_url":"https://mail.neelkamalindia.com/about-us.php"},
    {"name":"Hasnain Ansari","company":"BlueShine India","role":"Founder & CEO","industry":"Manufacturing / Exports / Fashion Accessories","email":"blueshineindia@gmail.com","contact_url":"https://www.blueshineindia.in/company-profile/","identity_url":"https://www.blueshineindia.in/about-me/"},
    {"name":"Sanjay Mehta","company":"MTC Group","role":"Director / Chairman","industry":"Metal Recycling / Manufacturing / International Trade","email":"mehtasanjay@mtcgroup.in","contact_url":"https://mrai.org.in/aboutmrai/boardofdirectors.html","identity_url":"https://www.mtcgroup.in/about-us.php"},
    {"name":"Sandeep Jain","company":"Sunalco Alloys Pvt. Ltd.","role":"Founder & Director","industry":"Aluminium Recycling / Manufacturing","email":"sandeep@sunalcoalloys.com","contact_url":"https://mrai.org.in/aboutmrai/boardofdirectors.html","identity_url":"https://www.sunalcoalloys.com/"},
    {"name":"Mohan Agarwal","company":"CMR Green Technologies Ltd.","role":"Co-Founder & Managing Director","industry":"Metal Recycling / Aluminium Manufacturing","email":"mohan.a@cmr.co.in","contact_url":"https://mrai.org.in/aboutmrai/boardofdirectors.html","identity_url":"https://cmr.co.in/"},
    {"name":"Anirudh Jhunjhunwala","company":"J.G. Chemicals Ltd.","role":"CEO, Managing Director & Director","industry":"Chemicals / Zinc Recycling / Manufacturing","email":"ajhunjhunwala@jgchem.com","contact_url":"https://mrai.org.in/aboutmrai/boardofdirectors.html","identity_url":"https://groww.in/stocks/jg-chemicals-ltd"},
    {"name":"Ashish Bansal","company":"Pondy Oxides & Chemicals Ltd.","role":"Managing Director & Executive Director","industry":"Chemicals / Metal Recycling / Manufacturing","email":"ashish@pocl.co.in","contact_url":"https://mrai.org.in/aboutmrai/boardofdirectors.html","identity_url":"https://www.bseindia.com/bseplus/AnnualReport/532626/5326260319.pdf"},
    {"name":"Gopal Gupta","company":"Laxcon Steels Ltd.","role":"Managing Director","industry":"Steel Manufacturing / Recycling","email":"gopal@gopalgroup.com","contact_url":"https://mrai.org.in/aboutmrai/boardofdirectors.html","identity_url":"https://www.laxconsteels.com/management/"},
    {"name":"Harsh Gandhi","company":"GRP Ltd.","role":"Executive Director","industry":"Reclaimed Rubber / Industrial Manufacturing","email":"harsh.gandhi@grpweb.com","contact_url":"https://mrai.org.in/aboutmrai/boardofdirectors.html","identity_url":"https://grpweb.com/"},
    {"name":"Dhawal Shah","company":"Metco Ventures LLP","role":"Managing Partner","industry":"Metals Recycling / Exports / Commodity Trading","email":"dhawal@metcoventures.com","contact_url":"https://mrai.org.in/aboutmrai/boardofdirectors.html","identity_url":"https://www.alcirclebiz.com/profile/metco-ventures-llp-16440"},
    {"name":"Jinesh Shah","company":"Rajhans Impex Pvt. Ltd.","role":"Director","industry":"Brass Manufacturing / Metals Import-Export","email":"jfs@rajhansimpex.com","contact_url":"https://mrai.org.in/aboutmrai/boardofdirectors.html","identity_url":"https://indiankanoon.org/doc/114140393/"},
    {"name":"Naveen Sharma","company":"Gravita India Ltd.","role":"Executive Director","industry":"Metal Recycling / Manufacturing / Exports","email":"navin@gravitaindia.com","contact_url":"https://mrai.org.in/aboutmrai/boardofdirectors.html","identity_url":"https://nsearchives.nseindia.com/corporate/GRAVITA_24102024163208_TranscriptFinal.pdf"},
    {"name":"Zain Nathani","company":"Nathani Group","role":"Managing Director","industry":"Ferrous Scrap / Exports / Recycling","email":"zain@nathanisteel.com","contact_url":"https://mrai.org.in/aboutmrai/boardofdirectors.html","identity_url":"https://www.bigmint.co/events/7thiiops-4thicoc-6thidsc/speakers/zain-nathani"},
    {"name":"Ehsan Gadawala","company":"Ala Group of Companies","role":"Chairman","industry":"Recycling / International Commodity Trading","email":"ehsan@alaindia.in","contact_url":"https://mrai.org.in/aboutmrai/boardofdirectors.html","identity_url":"https://api.mrai.org.in/Content/imrc/images/conference/PastConferenceDocs/Doc2/7thIMRC2020456.pdf"},
    {"name":"Keyur Shah","company":"Mono Steel India Ltd.","role":"CEO","industry":"Steel Manufacturing / Recycling","email":"kskeyurshah@gmail.com","contact_url":"https://mrai.org.in/aboutmrai/boardofdirectors.html","identity_url":"https://www.monosteel.co.in/"},
    {"name":"Devendra Surana","company":"Bhagyanagar India Ltd.","role":"Managing Director","industry":"Copper Manufacturing / Metals / Telecom","email":"devendra@surana.com","contact_url":"https://mrai.org.in/aboutmrai/boardofdirectors.html","identity_url":"https://bhagyanagarindia.com/company/"},
    {"name":"Rahul Goyal","company":"W2R / Waste2Resource","role":"Founder / CEO","industry":"Recycling / Circular Economy / Industrial Services","email":"ceo@w2r.co.in","contact_url":"https://mrai.org.in/aboutmrai/boardofdirectors.html","identity_url":"https://in.linkedin.com/in/rahul-goyal-2ba85b341"},
    {"name":"Saurabh Agarwal","company":"G N Motors / Re-Wire","role":"Founder / Director","industry":"Automotive Recycling / Vehicle Scrapping","email":"sourabh@gnmotors.net","contact_url":"https://mrai.org.in/aboutmrai/boardofdirectors.html","identity_url":"https://in.linkedin.com/company/ganganagar-vaahan-udyog-pvt-ltd"},
    {"name":"Rishi Mohan","company":"Catfin","role":"Founder & CEO","industry":"Fintech / Financial Services Distribution","email":"rishi@catfin.in","contact_url":"https://catfin.in/about","identity_url":"https://in.linkedin.com/in/rishi-mohan-65a6a037"},
    {"name":"Nishant Anshul","company":"Irin AI Pvt. Ltd.","role":"Founder & CEO","industry":"AI / Insurance Technology / SaaS","email":"nishant@irin.ai","contact_url":"https://delhi.tie.org/wp-content/uploads/2024/02/STPI-Leap-Ahead-Cohort-2024-Version-1.3.pdf","identity_url":"https://policygyani.com/about-us"},
    {"name":"Sandip Kumar Singh","company":"Ishitva Robotic Systems Pvt. Ltd.","role":"Co-Founder & CEO","industry":"AI / Industrial Automation / Recycling","email":"sandip@ishitva.in","contact_url":"https://startupmahakumbh.assocham.org/exhibitor_directory/exh_pdf/directory_A4.php?event_name=sm&event_year=2024","identity_url":"https://thekredible.com/company/ishitva/people"},
    {"name":"Manjeet Sandhu","company":"Indian Logistics","role":"Managing Partner","industry":"Logistics / Transport / Warehousing","email":"sandhu@indianlogistics.net","contact_url":"https://indianlogistics.net/","identity_url":"https://indianlogistics.net/about.html"},
    {"name":"Ritesh Maheshwari","company":"Shabro Metallic Pvt. Ltd.","role":"Executive Director, International Trade","industry":"Metals Recycling / International Trade","email":"ritesh@smtl.co.in","contact_url":"https://mrai.org.in/aboutmrai/boardofdirectors.html","identity_url":"https://www.jindalstainless.com/?p=6709"},
    {"name":"Jayant Jain","company":"G.R. Metalloys Pvt. Ltd.","role":"Managing Director","industry":"Aluminium Alloys / Manufacturing / Metals Trade","email":"jayant@grmetal.in","contact_url":"https://mrai.org.in/aboutmrai/boardofdirectors.html","identity_url":"https://business-summit.mrai.org.in/assets/pdf/IBS-PCR-CUT_compressed.pdf"},
    {"name":"Shravan Aggarwal","company":"Guardian Castings Pvt. Ltd.","role":"Founder & CEO","industry":"Steel Manufacturing / TMT Bars","email":"shravan@guardiancastings.com","contact_url":"https://mrai.org.in/aboutmrai/boardofdirectors.html","identity_url":"https://www.theindustryoutlook.com/manufacturing/vendor/guardian-castings-combining-innovation-with-precision-in-tmt-bar-manufacturing-cid-13140.html"},
    {"name":"B. K. Soni","company":"Eco Recycling Ltd. (Ecoreco)","role":"Founder / Executive Chairman & Managing Director","industry":"E-waste Recycling / Circular Economy","email":"bksoni@ecoreco.com","contact_url":"https://mrai.org.in/aboutmrai/boardofdirectors.html","identity_url":"https://bsmedia.business-standard.com/_media/bs/data/announcements/bse/19082024/fdb3f730-2b5f-436e-b2af-16bd180b9411.pdf"},
    {"name":"Ulhas Parlikar","company":"Industrial Symbiosis for Circular Economy (ISCE)","role":"Founder / Global Consultant","industry":"Circular Economy / Industrial Waste Management","email":"ulhas.parlikar@gmail.com","contact_url":"https://mrai.org.in/aboutmrai/boardofdirectors.html","identity_url":"https://ulhas.parlikar.com/services/"},
    {"name":"Karan Chugh","company":"Eknaam Printers and Packers","role":"Founder & CEO","industry":"Seed Packaging / Printing / Exports","email":"eknaam.printers@gmail.com","contact_url":"https://nsai.co.in/storage/app/media/SEED-TIMES-sep-dec-2023.pdf","identity_url":"https://www.eknaampackaging.in/profile.html"},
    {"name":"Ramratan Singhi","company":"SURE Group / Sure Logitrans Pvt. Ltd.","role":"Founder & CEO","industry":"Industrial Packaging / Logistics / Trucking","email":"ram@palletcovers.in","contact_url":"https://sites.google.com/suregroup.in/pallet-innovations/team","identity_url":"https://www.motorindiaonline.in/sure-logitrans-engineering-reliability-and-safety-in-modern-trucking/"},
    {"name":"Adnan Ahmad","company":"Arena Cargo and Logistics India Pvt. Ltd.","role":"Founder & CEO","industry":"Logistics / Freight Forwarding / Supply Chain","email":"adnan@arenalogistics.co.in","contact_url":"https://www.adnanahmad.in/","identity_url":"https://arenalogistics.co.in/about-md-ceo/"},
    {"name":"Ankush Thube","company":"Agrifora Pvt. Ltd.","role":"Founder & CEO","industry":"Agri-inputs / Chemicals / Exports","email":"ankush.thube@agrifora.in","contact_url":"https://eoiaddisababa.gov.in/wp-content/uploads/2024/01/Trade-Queries-from-India-for-December-2023.pdf","identity_url":"https://www.zaubacorp.com/AGRIFORA-PRIVATE-LIMITED-U01100PN2021PTC201360"},
    {"name":"Asoke Kumar Ghosh","company":"Sarathi Exim Pvt. Ltd.","role":"Founder & CEO","industry":"Agricultural Exports / International Trade","email":"ak.ghosh@sarathiexim.com","contact_url":"https://mostpp.ru/upload/medialibrary/992/x2uclz56qyiy5bzl0ur3qnm7a32ggu3j/Profile-of-FIEO-Delegates-.pdf","identity_url":"https://www.tofler.in/sarathi-exim-private-limited/company/U74900WB2015PTC207586"},
    {"name":"Sandeep Rungta","company":"Balaji Export Corporation","role":"Founder & CEO","industry":"Leather Manufacturing / Exports","email":"sandeep@balajiexport.com","contact_url":"https://www.ilpaindia.org/wp-content/uploads/2018/07/ILPA-MS-LIST.pdf","identity_url":"https://www.balajiexport.com/about"},
    {"name":"Manoj Bhatu Patil","company":"Cruxzen Technologies Pvt. Ltd.","role":"Founder & Director","industry":"B2B Software / Seafood Export Operations","email":"manoj.patil@cruxzen.tech","contact_url":"https://mpeda.gov.in/wp-content/uploads/2023/03/MNL-December-2022-FOR-WEB.pdf","identity_url":"https://www.indiafilings.com/search/cruxzen-technologies-private-limited-cin-U74990PN2019PTC187583"},
    {"name":"Piyush Pravin Raisoni","company":"Roast Foods / Myvi Foods Pvt. Ltd.","role":"Founder","industry":"Food Manufacturing / Consumer Products / Exports","email":"piyush@roastfoods.com","contact_url":"https://www.eoilisbon.gov.in/docs/1673328926List%20of%20exporters%20Participants%20_BSM%202023.xlsx%20-%20Sheet1.pdf","identity_url":"https://apeda.gov.in/sites/default/files/report_on_trade_events/Report_Belgium_Post_Event_2.pdf"},
    {"name":"Purnima Khandelwal","company":"INI Farms Pvt. Ltd.","role":"Co-Founder & CEO","industry":"Agriculture / Horticulture Exports / Supply Chain","email":"purnima.khandelwal@inifarms.com","contact_url":"https://www.eoilisbon.gov.in/docs/1673328926List%20of%20exporters%20Participants%20_BSM%202023.xlsx%20-%20Sheet1.pdf","identity_url":"https://www.yourstory.com/herstory/2020/04/woman-entrepreneur-horticulture-ini-farms-india"},
    {"name":"Pradyumna Raj Agrahari","company":"NextOn Foods Pvt. Ltd.","role":"Managing Director & CEO","industry":"Food Manufacturing / Exports / Supply Chain","email":"pradyumna.agrahari@nextonfoods.com","contact_url":"https://www.eoilisbon.gov.in/docs/1673328926List%20of%20exporters%20Participants%20_BSM%202023.xlsx%20-%20Sheet1.pdf","identity_url":"https://www.planetexim.net/indian-company/directors/nexton-foods-private-limited/cin/U74999PN2017PTC172078.html"},
    {"name":"K. V. Rama Subba Reddy","company":"Sattva Millets and Food Products / Mibbles","role":"Founder","industry":"Food Manufacturing / Millets / Agritech","email":"kvrs.reddy@gmail.com","contact_url":"https://www.eoilisbon.gov.in/docs/1673328926List%20of%20exporters%20Participants%20_BSM%202023.xlsx%20-%20Sheet1.pdf","identity_url":"https://mibbles.in/our-story/"},
    {"name":"Pankaj Agarwal","company":"Treta Agro Pvt. Ltd. / Just Organik","role":"Co-Founder & Managing Director","industry":"Organic Food Manufacturing / Agriculture / Exports","email":"pankaj@justorganik.com","contact_url":"https://www.eoilisbon.gov.in/docs/1673328926List%20of%20exporters%20Participants%20_BSM%202023.xlsx%20-%20Sheet1.pdf","identity_url":"https://www.inclusivecapitalism.com/member/pankaj-agarwal/"},
    {"name":"Yosha Gupta","company":"MeMeraki","role":"Founder & CEO","industry":"Fintech / Culture Technology / E-commerce","email":"yosha.gupta@memeraki.com","contact_url":"https://handicrafts.gov.in/CmsUpload/18112025011157DCH%20Strategy%20Document.pdf","identity_url":"https://www.memeraki.com/pages/about-us"},
    {"name":"Venkateshwarlu Madala","company":"CIBERTS / CIBERTSAI","role":"Founder & CEO","industry":"AI / Cybersecurity / Compliance Technology","email":"venkatmadala@ciberts.com","contact_url":"https://indianchamber.org/upload/page/pdf/sstarupreneur-sept2025-w1.pdf","identity_url":"https://www.thecompanycheck.com/company/b/ciberts/6152919bce1e41f4a"},
    {"name":"Dr. Pawan Saharan","company":"Biomix Network Ltd.","role":"Founder & CEO","industry":"Pharma / Biotechnology / Healthcare","email":"drpawan@biomix.in","contact_url":"https://www.biomix.in/images/pdf/inventor-biography.pdf","identity_url":"https://biomix.in/images/pdf/health-for-all-problems-and-solutions-to-pandemics-final.pdf"},
    {"name":"Sateesh Dasari","company":"Continuum AI Global Pvt. Ltd.","role":"Co-Founder & CEO","industry":"AI / Enterprise Automation / Software","email":"sateesh@continuumai.io","contact_url":"https://continuumai.io/about-us-continuum-ai/","identity_url":"https://continuumai.io/deep-dive-what-makes-an-enterprise-ai-application-truly-transformative/"},
    {"name":"Rohit Grover","company":"Aerostrovilos Energy Pvt. Ltd.","role":"Co-Founder & CEO","industry":"Industrial Manufacturing / Clean Energy / Gas Turbines","email":"rohit@aerostrovilos.com","contact_url":"https://www.iitm.ac.in/sites/default/files/Others/arira-2021.pdf","identity_url":"https://www.forbesindia.com/article/innovation/aerostrovilos-energy-aiming-to-be-the-tesla-of-micro-gas-turbines/89109/1"},
    {"name":"Pradeep Thangappan","company":"Aerostrovilos Energy Pvt. Ltd.","role":"Co-Founder & COO","industry":"Industrial Manufacturing / Clean Energy / Gas Turbines","email":"pradeep@aerostrovilos.com","contact_url":"https://www.indiafilings.com/search/aerostrovilos-energy-private-limited-cin-U29308KA2017PTC104608","identity_url":"https://www.forbesindia.com/article/innovation/aerostrovilos-energy-aiming-to-be-the-tesla-of-micro-gas-turbines/89109/1"},
    {"name":"Ankit Poddar","company":"ZedBee Technologies Pvt. Ltd.","role":"Founder & CEO","industry":"AI / IoT / Industrial Energy Management","email":"ankit@swadhaenergies.com","contact_url":"https://www.iitm.ac.in/sites/default/files/Others/ariia-2020.pdf","identity_url":"https://rtbi.in/incubationiitm/portfolio.html"},
    {"name":"Vinay Mallapur","company":"DeVault Inc.","role":"Founder & CEO","industry":"Precision Engineering / Industrial Automation / Manufacturing","email":"devault.inc@gmail.com","contact_url":"http://devaultinc.in/spm/","identity_url":"https://in.linkedin.com/in/vinay-mallapur-19322222"},
    {"name":"Shiv S. Saxena","company":"Saturn International","role":"Founder & CEO","industry":"Precision Engineering / Manufacturing / Exports","email":"sssaxena@saturn.org.in","contact_url":"https://saturn.org.in/about-us/","identity_url":"https://saturn.org.in/"},
    {"name":"Jennifer Pandiyan","company":"Thales Cleantech (OPC) Pvt. Ltd.","role":"Founder & CEO","industry":"Clean Technology / Water-Energy Systems / Manufacturing","email":"mailme.jenny@gmail.com","contact_url":"https://www.indiafilings.com/search/thales-cleantech-opc-private-limited-cin-U41000TN2021OPC141631","identity_url":"https://www.thalescleantech.com/about"},
    {"name":"Arun Pandit","company":"Hyphen SCS Private Limited","role":"Co-Founder","industry":"Logistics / Warehousing / Fulfillment Technology","email":"arunpandit@hyphenscs.com","contact_url":"https://www.startupindia.gov.in/nsa5.0results/Visionary-Award-for-Infrastructure-Excellence.html","identity_url":"https://arunpandit.com/who-is-arun-pandit/"},
    {"name":"Dhananjay Goel","company":"Timble Technologies Private Limited","role":"Founder & CEO","industry":"Fintech / AI / Financial Compliance","email":"dhananjay@timbletech.com","contact_url":"https://www.startupindia.gov.in/nsa5.0results/Fintech-Revolution-Catalyst-Award.html","identity_url":"https://www.theceo.in/amp/story/industry/technology/timble-technologies-delivering-impact-with-advanced-artificial-intelligence-technology"},
    {"name":"Aishwarya Karnataki","company":"Glovatrix Private Limited","role":"Founder & CEO","industry":"AI / Assistive Technology / Deep Tech","email":"aishwarya@glovatrix.org","contact_url":"https://www.startupindia.gov.in/nsa5.0results/Inclusive-Design-Excellence-Award.html","identity_url":"https://in.linkedin.com/in/aishwarya-karnataki-608191b6"},
    {"name":"Dr. Harsh V. Sethi","company":"TriNANO Technologies Pvt. Ltd.","role":"Founder & CEO","industry":"Industrial Materials / Clean Energy / Nanotechnology","email":"harsh_sethi@tri-nano.co","contact_url":"https://challenge.greenhouse.tech/media/download/13c14defa6b60eae75f02e70df6a27df","identity_url":"https://tri-nano.co/our-team/"},
    {"name":"Dr. Priyadarshini Sanyal","company":"Proxi Farma Private Limited / Potion1st","role":"Co-Founder","industry":"Pharma / Food Technology / Nutrition","email":"pia.sanyal@potion1st.com","contact_url":"https://www.startupindia.gov.in/nsa5.0results/F%26B-Trailblazer-Award.html","identity_url":"https://www.ynos.in/startup/potion-1st-464795"},
    {"name":"Phanindra Gopala Krishna","company":"Frenvi Private Limited","role":"Founder & CEO","industry":"Manufacturing / Sustainable Packaging / Food Technology","email":"phanindra@frenvi.de","contact_url":"https://www.indiafilings.com/search/frenvi-private-limited-cin-U37100KA2020PTC138065","identity_url":"https://frenvi.in/about-us/"},
    {"name":"Randeep Singh","company":"Aurafox Solutions / Commutec","role":"Founder & CEO","industry":"Logistics / Corporate Mobility / Fleet Operations","email":"randeep@aurafox.com","contact_url":"https://www.indiafilings.com/search/aurafox-solutions-private-limited-cin-U74999MH2016PTC287864","identity_url":"https://www.commutec.in/about"},
    {"name":"Akanksha Priyadarshini","company":"Aurassure Private Limited","role":"Founder & CEO","industry":"AI / Climate Intelligence / Smart Infrastructure","email":"akanksha@aurassure.com","contact_url":"https://www.reset.build/directory/monitors/rm-060","identity_url":"https://aurassure.com/about-us/"},
    {"name":"Dr. Giriraj Ratan Chandak","company":"Lightening Lives LLP","role":"Founder & CEO","industry":"Pharma / Biotechnology / Diagnostics","email":"chandakgrc@lighteninglives.in","contact_url":"https://dbt.gov.in/Vigyan.pdf","identity_url":"https://lighteninglives.in/about-us.php"},
    {"name":"Rajnish Jain","company":"Avani Bio Energy / Avani","role":"Founder & CEO","industry":"Clean Energy / Rural Manufacturing / Sustainable Livelihoods","email":"rajnish@avani-kumaon.org","contact_url":"https://psa.gov.in/CMS/web/sites/default/files/psa_custom_files/UpLink%20Top%20Innovators%20-%20India%20Cohort.pdf","identity_url":"https://avani-kumaon.org/team/"},
    {"name":"Shailie Mehta","company":"Acacia Eco Plantation Services LLP","role":"Co-Founder & CEO","industry":"Climate Technology / Urban Forestry / Sustainable Operations","email":"shailie.mehta@acaciaeco.com","contact_url":"https://psa.gov.in/CMS/web/sites/default/files/psa_custom_files/UpLink%20Top%20Innovators%20-%20India%20Cohort.pdf","identity_url":"https://mediusearth.com/"},
    {"name":"Gaurav Parmar","company":"Orgro Fibre LLP","role":"Founder & CEO","industry":"Sustainable Packaging / Manufacturing / Agro-waste Materials","email":"orgroindia@gmail.com","contact_url":"https://psa.gov.in/CMS/web/sites/default/files/psa_custom_files/UpLink%20Top%20Innovators%20-%20India%20Cohort.pdf","identity_url":"https://www.indiafilings.com/search/orgro-fibre-llp-AAP-2057"},
    {"name":"Jitendra Sinha","company":"SAI Sustainable Agro","role":"Co-Founder & CEO","industry":"Agriculture / Rural Supply Chains / Sustainable Enterprise","email":"jitendraksinha@hotmail.com","contact_url":"https://psa.gov.in/CMS/web/sites/default/files/psa_custom_files/UpLink%20Top%20Innovators%20-%20India%20Cohort.pdf","identity_url":"https://alumni.ucd.ie/magazine/2023/nature-restored/"},
]


def resolves(domain: str) -> bool:
    try:
        result = subprocess.run(["dig", "+time=3", "+tries=1", "+short", domain], capture_output=True, text=True, timeout=5, check=False)
        if result.stdout.strip():
            return True
        # Some mail-only domains publish MX records without an A/AAAA record.
        mx_result = subprocess.run(["dig", "+time=3", "+tries=1", "+short", "MX", domain], capture_output=True, text=True, timeout=5, check=False)
        return bool(mx_result.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        return False


def mx(domain: str) -> list[str]:
    try:
        p = subprocess.run(["dig", "+short", "MX", domain], capture_output=True, text=True, timeout=8, check=False)
        return [x.strip() for x in p.stdout.splitlines() if x.strip()]
    except Exception:
        return []


@contextmanager
def bounded_fetch(seconds: int = 20):
    def alarm_handler(signum, frame):
        raise TimeoutError(f"source fetch exceeded {seconds}s")
    old = signal.signal(signal.SIGALRM, alarm_handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    selected = SEEDS
    requested = {x.strip().lower() for x in os.getenv("SEED_NAMES", "").split(",") if x.strip()}
    if requested:
        selected = [x for x in SEEDS if x["name"].lower() in requested]
    existing_records = {}
    if os.getenv("MERGE_EXISTING") == "1" and (OUT / "manual_seed_validation.json").exists():
        try:
            existing_records = {x["name"].lower(): x for x in json.loads((OUT / "manual_seed_validation.json").read_text(encoding="utf-8")).get("records", [])}
        except Exception:
            existing_records = {}
    rows = []
    for seed in selected:
        row = {**seed, "checked_at": datetime.now(timezone.utc).isoformat(), "status":"rejected", "mailbox_status":"not_tested", "checks":{}, "evidence":[]}
        try:
            with bounded_fetch(20):
                contact = fetch_source(seed["contact_url"], timeout=12, max_bytes=30_000_000)
            with bounded_fetch(20):
                identity = fetch_source(seed["identity_url"], timeout=12, max_bytes=30_000_000)
            email = seed["email"].lower()
            name = re.sub(r"[^a-z0-9]+", " ", seed["name"].lower()).strip()
            normalize = lambda text: re.sub(r"[^a-z0-9]+", " ", text.lower())
            row["evidence"] = [{"source_id":contact.source_id,"url":contact.url,"excerpt":" ".join(contact.text[:2000].split())}, {"source_id":identity.source_id,"url":identity.url,"excerpt":" ".join(identity.text[:2000].split())}]
            compact = lambda text: re.sub(r"[^a-z0-9]+", "", text.lower())
            name_tokens = [x for x in name.split() if len(x) > 1]
            contact_norm = normalize(contact.text)
            identity_norm = normalize(identity.text)
            contact_compact = compact(contact.text)
            identity_compact = compact(identity.text)
            name_compact = compact(seed["name"])
            contact_name_match = name in contact_norm or (all(t in contact_norm.split() for t in name_tokens) if name_tokens else False) or name_compact in contact_compact
            identity_name_match = name in identity_norm or (all(t in identity_norm.split() for t in name_tokens) if name_tokens else False) or name_compact in identity_compact
            row["checks"] = {
                "syntax": bool(re.fullmatch(r"[^\s@*]+@[^\s@*]+\.[^\s@*]+", email)),
                "exact_email_in_contact_source": email in contact.text.lower(),
                "name_in_contact_source": contact_name_match,
                "name_in_identity_source": identity_name_match,
                "independent_source_urls": seed["contact_url"] != seed["identity_url"],
                "domain_resolves": resolves(email.rsplit("@",1)[1]),
                "mx_present": bool(mx(email.rsplit("@",1)[1])),
            }
            if all(row["checks"].values()):
                row["status"] = "strict_public_contact_verified"
                row["mailbox_status"] = "domain_accepts_mail_mailbox_unconfirmed"
            else:
                row["rejection_reasons"] = [k for k,v in row["checks"].items() if not v]
        except Exception as exc:
            row["rejection_reasons"] = [f"source_fetch_failed:{str(exc)[:300]}"]
        rows.append(row)
        existing_records[seed["name"].lower()] = row
        # Persist after every candidate so a slow or failing source never
        # destroys progress and the queue can be resumed safely.
        merged_rows = list(existing_records.values())
        accepted_so_far = [x for x in merged_rows if x["status"] == "strict_public_contact_verified"]
        (OUT / "manual_seed_validation.checkpoint.json").write_text(json.dumps({"status":"checkpoint","verified_count":len(accepted_so_far),"records":merged_rows}, indent=2, ensure_ascii=False), encoding="utf-8")
    final_rows = list(existing_records.values()) if os.getenv("MERGE_EXISTING") == "1" else rows
    accepted = [x for x in final_rows if x["status"] == "strict_public_contact_verified"]
    (OUT / "manual_seed_validation.json").write_text(json.dumps({"status":"manual_seed_validation","verified_count":len(accepted),"mailboxes_confirmed":0,"records":final_rows},indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({"status":"manual_seed_validation","verified_count":len(accepted),"rejected_count":len(final_rows)-len(accepted),"mailboxes_confirmed":0,"output":str(OUT/'manual_seed_validation.json')}))


if __name__ == "__main__":
    main()
