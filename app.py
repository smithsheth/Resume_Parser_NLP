from flask import Flask, render_template,request, session 
import os
import pickle
from werkzeug.utils import secure_filename
from resumeExtraction import resumeExtraction
from resumeScreener import resumeScreener
import sys,fitz,docx2txt
import path
import pathlib
import requests
import pandas as pd

app = Flask(__name__)

extractorObj = pickle.load(open("resumeExtractor.pkl","rb"))
screenerObj = pickle.load(open("resumeScreener.pkl","rb"))
job_compare_obj = pickle.load(open("jd_profile_comparison.pkl","rb"))

def extractData(file,ext):
    text=""
    if ext=="docx": 
        temp = docx2txt.process(file)
        text = [line.replace('\t', ' ') for line in temp.split('\n') if line]
        text = ' '.join(text)
    if ext=="pdf":
        for page in fitz.open(file):
            text = text + str(page.get_text())
        text = " ".join(text.split('\n'))

    outtext=extractorObj.extract_skills(text)

    return outtext

class my_dictionary(dict): 
  
    # __init__ function 
    def __init__(self): 
        self = dict() 
          
    # Function to add key:value 
    def add(self, key, value): 
        self[key] = value 
  

@app.route("/")
def index():
    return render_template("main.html")      
 
@app.route("/individual") 
def individual():
    return render_template("individual.html")    

@app.route("/checkDetails", methods=['POST'])
def checkDetails():
    res_ind_data=""
    if request.method == "POST":
    
        job_ind_data=request.form["job"]
        res_ind_data=request.form["res"]
        clean_j=extractorObj.clean_text(job_ind_data)
        job_data=extractorObj.extract_skills(clean_j)
        print("####",job_data)
        clean_r=extractorObj.clean_text(res_ind_data)
        res_data=extractorObj.extract_skills(clean_r)
        print("####",res_data)
        match_percentage = job_compare_obj.match(str(job_data),str(res_data))

    return render_template("individual.html",percentage=match_percentage)

@app.route("/company") 
def company():
    return render_template("get_results.html")    

@app.route("/checkResume", methods=['POST'])
def checkResume():
    jobpath="static/jobdes/"
    for i in os.listdir(jobpath):
        jobdata=extractData(jobpath+i,i.rsplit('.',1)[1].lower())
        print("Jobdata",jobdata)
        filename = (i.split(os.path.sep)[-1]).split('.')[0] 
        output_file1 = os.path.join('extracted/Jobdata', '{}.txt'.format(filename))
        txt_file=open(output_file1,'w')
        row="".join([str(jobdata)])
        txt_file.write(row + "\n")
        txt_file.close() 
    
    resumepath="static/resumes/" 
    for i in os.listdir(resumepath):
        print("1",i)
        fetchedData=extractorObj.extractorData(resumepath+i,i.rsplit('.',1)[1].lower())
        # skillsPercentage = screenerObj.screenResume(fetchedData[5])
        print("FetchedData:",fetchedData)
        filename = (i.split(os.path.sep)[-1]).split('.')[0] 
        output_file1 = os.path.join('extracted/Resumedata', '{}.txt'.format(filename))
        txt_file=open(output_file1,'w')
        row2="".join([str(fetchedData[3])])
        txt_file.write(row2 + "\n")
        txt_file.close()   

 
    con_job_path="extracted/Jobdata/"
    dataframes=[]
    todict={}
    jobs=[]
    dict_obj = my_dictionary()
    for i in os.listdir(con_job_path):
        job_file=open(con_job_path + i, "r")
        job=job_file.read()   
        print("###res###",job)
        jobfilename = (i.split(os.path.sep)[-1]).split('.')[0] 
        jobs.append(jobfilename)
        resume_names=[]
        resume_scores=[]
        for i in os.listdir(resumepath):   
            filename = (i.split(os.path.sep)[-1]).split('.')[0] 
            resume_names.append(filename)
            resume_file = open("extracted/Resumedata/"+filename+".txt", "r")
            resume = resume_file.read()
            print("###res###",resume)
            match_percentage = job_compare_obj.match(job,resume)
            resume_scores.append(match_percentage)
            print(filename,match_percentage)

        col1="Resume_List"    
        col2="Skill Matching %"
        dataframe = pd.DataFrame({col1:resume_names,col2:resume_scores})
        sorted_df = dataframe.sort_values(by='Skill Matching %', ascending=False,ignore_index=True)
        print(sorted_df)
        with pd.ExcelWriter('job_match.xlsx',
                        mode='w') as writer:  
            sorted_df.to_excel(writer, sheet_name='sheet1', index=False)
        dataframe=sorted_df.to_html()
        dataframes.append(dataframe)
        
        # Main Function 
         
        d= dict()
        dict_obj.key = jobfilename
        dict_obj.value = dataframe
        
        dict_obj.add(dict_obj.key, dict_obj.value) 
        
    print(dict_obj) 

    # print(dataframes)    
    return render_template("get_results.html",listofdict=dict_obj,d=d)
         
if __name__=="__main__":
    app.run(debug=True)