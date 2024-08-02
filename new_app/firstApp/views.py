from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .forms import UploadFileForm
import pandas as pd
from .models import UploadedFile
import numpy as np
from datetime import *

from django.http import FileResponse


def clean_column_name(col_name):
    return ' '.join(col_name.split())

def transform_data(input_excel,input_file_path):
    master_file_path = 'master.xlsx'
    master_df = pd.read_excel(master_file_path)
    input_file = pd.ExcelFile(input_file_path)
    master_product=pd.read_excel(master_file_path,sheet_name ="lob",index_col =0)

    master_category=pd.read_excel(master_file_path,sheet_name = "category")
    master_product.columns = master_product.columns.str.strip()
    master_df.columns = master_df.columns.str.strip()
    master_product.reset_index(inplace = True)
    master_category.columns = master_category.columns.str.strip()
    product_Arr=master_product['All Other miscellaneous'].to_numpy()
    product_Arr=np.append(product_Arr,'All Other miscellaneous')
    for i in range(len(product_Arr)):
            product_Arr[i]=clean_column_name(product_Arr[i])
    print(product_Arr)
    all_data = []

    for sheet_name in input_file.sheet_names:
        if sheet_name == 'Health Portfolio':
            row=[0,1,3]
        elif sheet_name == 'Liability Portfolio':
            row=[0,1,3]
        elif sheet_name=='Miscellaneous portfolio':
            row=[0]
        elif sheet_name=='Segmentwise Report':
            row=[0]
        sheet_df = pd.read_excel(input_file, sheet_name=sheet_name,index_col=0,skiprows=row)
        sheet_df.columns = [clean_column_name(col) for col in sheet_df.columns]    # Clean the column names
        sheet_df.reset_index(inplace = True)
        sheet_df.columns.values[0]='insurer'
        columns_to_include = [col for col in sheet_df.columns if col in product_Arr or col == 'insurer']
        sheet_df = sheet_df[columns_to_include]

        all_data.append(sheet_df)
    final_df = pd.concat(all_data, ignore_index=True)
    mapping_dict = pd.Series(master_df.clubbed_name.values, index=master_df.insurer).to_dict()
    mapping_category=pd.Series(master_category.category.values, index=master_category.clubbed_name).to_dict()

    final_df['clubbed_name'] = final_df['insurer'].map(mapping_dict)
    final_df['category'] = final_df['clubbed_name'].map(mapping_category)


    rows_dict=[]
    for index,row in final_df.iterrows():
        rows_dict.append(row.to_dict())

    print(len(rows_dict[0]))

    output_data=[]
    last_clubbed_name=""
    last_category=""
    for i in range(len(rows_dict)):
        output_row={}
        if rows_dict[i]['insurer']=="Previous Year":
            for key,value in rows_dict[i].items():
                output_row={}
                if key=='insurer' or key=='clubbed_name' or key=='category':
                    continue
                else:
                    output_row={"Year":2022,
                      "Month":"Dec",
                        "clubbed_name":last_clubbed_name,
                        "category":last_category,
                        "Product":key,
                        "Value":value
                        }
                output_data.append(output_row)
        else:
            for key,value in rows_dict[i].items():
                output_row={}
                if rows_dict[i]['clubbed_name']!=np.nan:
                    last_clubbed_name=rows_dict[i]['clubbed_name']
            
                if rows_dict[i]['category']!=np.nan:
                    last_category=rows_dict[i]['category']

                if key=='insurer' or key=='clubbed_name' or key=='category':
                    continue
                else:
                    output_row={"Year":2023,
                      "Month":"Dec",
                        "clubbed_name":last_clubbed_name,
                        "category":last_category,
                        "Product":key,
                        "Value":value
                        }
                output_data.append(output_row)
    output_df=pd.DataFrame(output_data)
    output_df=output_df.sort_values(['clubbed_name','Year',"Product"])
    output_df.fillna(0)
    

    output_file_path = input_file_path.replace('uploads/', 'outputs/')
    output_df.to_excel(output_file_path, index=False)
    return output_df,output_file_path
# Create your views here.
def home(request):
    if request.method == "POST":
        form=UploadFileForm(request.POST,request.FILES)
        if form.is_valid():
            uploaded_file = form.save()
            input_file_path = uploaded_file.input_file.path
            input1=request.FILES.get('input1')
            transformed_df,output_file_path=transform_data(input1,input_file_path)

            uploaded_file.output_file.name = output_file_path
            uploaded_file.save()
            file_path = uploaded_file.output_file.path  # Absolute path to the file
    
            response = FileResponse(open(file_path, 'rb'))
            response['Content-Disposition'] = f'attachment; filename="{uploaded_file.output_file.name}"'
            return response
            
    else:
        form=UploadFileForm()
        return render(request,"home.html",{"form":form})


@api_view(['GET'])
def Api_Response(request):
    msg="Response"
    return Response({"msg":msg})