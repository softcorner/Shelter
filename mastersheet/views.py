
from django.shortcuts import render
from django.http import HttpResponse
from mastersheet.forms import find_slum
from mastersheet.models import *

from itertools import chain

from master.models import *
from django.views.decorators.csrf import csrf_exempt

import json

import urllib2

#The views in this file correspond to the mastersheet functionality of shelter app.


# 'masterSheet()' is the principal view.
# It collects the data from newest version of RHS form and family factsheets
# Also, it retrieves the data of accounts and SBM. This view bundles them in a single object
# to be displayed to the front end.
@csrf_exempt
def masterSheet(request, slum_code = 0 ):
    print "$$$$$$ In masterSheet view.... $$$$$$$$$$$"


    if "slumname" in str(request.POST.get('form')):
        delimiter = 'slumname='
        slum_code = Slum.objects.filter(pk = int(request.POST.get('form').partition(delimiter)[2]) ).values_list("shelter_slum_code", flat = True)
        print slum_code

    # Hitting Kobo urls to fetch data of RHS, family factsheet and data of RHS form

    urlv = 'http://kc.shelter-associates.org/api/v1/data/130?query={"slum_name":"273425265502"}'
    url_family_factsheet = 'https://kc.shelter-associates.org/api/v1/data/68?format=json&query={"group_vq77l17/slum_name":"273425267703"}&fields=["OnfieldFactsheet","group_ne3ao98/Have_you_upgraded_yo_ng_individual_toilet","group_ne3ao98/Cost_of_upgradation_in_Rs","group_ne3ao98/Where_the_individual_ilet_is_connected_to","group_ne3ao98/Use_of_toilet","group_vq77l17/Household_number"]'
    url_RHS_form = "https://kc.shelter-associates.org/api/v1/forms/130/form.json"


    #print ("Sending Request to", url_family_factsheet)
    kobotoolbox_request = urllib2.Request(urlv)
    kobotoolbox_request_family_factsheet = urllib2.Request(url_family_factsheet)
    kobotoolbox_request_RHS_form = urllib2.Request(url_RHS_form)


    kobotoolbox_request.add_header('Authorization', "OAuth2 c213f2e7a3221171e8dd501f0fd8153ad95ecd93 ")
    kobotoolbox_request_family_factsheet.add_header('Authorization', "OAuth2 c213f2e7a3221171e8dd501f0fd8153ad95ecd93 ")
    kobotoolbox_request_RHS_form.add_header('Authorization', "OAuth2 c213f2e7a3221171e8dd501f0fd8153ad95ecd93 ")


    res = urllib2.urlopen(kobotoolbox_request)
    res_family_factsheet = urllib2.urlopen(kobotoolbox_request_family_factsheet)
    res_RHS_form = urllib2.urlopen(kobotoolbox_request_RHS_form)

    html = res.read()
    html_family_factsheet = res_family_factsheet.read()
    html_RHS_form = res_RHS_form.read()

    formdict = json.loads(html)
    formdict_family_factsheet =json.loads(html_family_factsheet)
    formdict_RHS_form = json.loads(html_RHS_form)
    name_label_data = []
    try:
        for i in formdict_RHS_form['children']:
            temp_data = trav(i) # trav() function traverses the dictionary to find last hanging child
            name_label_data.extend(temp_data)
    except Exception as e:
        print e
    # arranging data with respect to household numbers
    temp_FF={obj_FF['group_vq77l17/Household_number'] : obj_FF for obj_FF in formdict_family_factsheet}

    temp_FF_keys = temp_FF.keys()
    for x in formdict:
        if x['Household_number'] in temp_FF_keys:
            x.update(temp_FF[x['Household_number']])
            x['OnfieldFactsheet'] = 'Yes'

    toilet_reconstruction_fields = ['slum', 'household_number','agreement_date_str','agreement_cancelled','septic_tank_date_str','phase_one_material_date_str','phase_two_material_date_str','phase_three_material_date_str','completion_date_str','status','comment','material_shifted_to']
    daily_reporting_data = ToiletConstruction.objects.extra(select={'phase_one_material_date_str':"to_char(phase_one_material_date, 'YYYY-MM-DD HH24:MI:SS')",
                                                                    'phase_two_material_date_str': "to_char(phase_two_material_date, 'YYYY-MM-DD HH24:MI:SS')",
                                                                    'phase_three_material_date_str': "to_char(phase_three_material_date, 'YYYY-MM-DD HH24:MI:SS')",
                                                                    'septic_tank_date_str': "to_char(septic_tank_date, 'YYYY-MM-DD HH24:MI:SS')",
                                                                    'agreement_date_str': "to_char(agreement_date, 'YYYY-MM-DD HH24:MI:SS')",
                                                                    'completion_date_str': "to_char(completion_date, 'YYYY-MM-DD HH24:MI:SS')"}).filter(slum__shelter_slum_code=273425265502)
    daily_reporting_data = daily_reporting_data.values(*toilet_reconstruction_fields)

    temp_daily_reporting = {obj_DR['household_number']: obj_DR for obj_DR in daily_reporting_data}
    temp_DR_keys = temp_daily_reporting.keys()


    try:
        for x in formdict:
            if x['Household_number'] in temp_DR_keys:
                x.update(temp_daily_reporting[x['Household_number']])
    except Exception as err:
        print err

    sbm_fields = ['slum', 'household_number', 'name', 'application_id', 'photo_uploaded', 'created_date_str']
    sbm_data = SBMUpload.objects.extra(select={'created_date_str': "to_char(created_date, 'YYYY-MM-DD HH24:MI:SS')"}).filter(slum__shelter_slum_code=273425265502)
    sbm_data = sbm_data.values(*sbm_fields)

    temp_sbm = {obj_DR['household_number']: obj_DR for obj_DR in sbm_data}
    temp_sbm_keys = temp_sbm.keys()
    try:
        for x in formdict:
            if x['Household_number'] in temp_sbm_keys:
                x.update(temp_sbm[x['Household_number']])
    except Exception as err:
        print err

    community_mobilization_fields = ['slum', 'household_number','activity_type','activity_date_str']
    community_mobilization_data = CommunityMobilization.objects.extra(select={'activity_date_str': "to_char(activity_date, 'YYYY-MM-DD HH24:MI:SS')"}).filter(slum__shelter_slum_code=273425265502)
    community_mobilization_data1 = community_mobilization_data.values(*community_mobilization_fields)
    community_mobilization_data_list = list(community_mobilization_data1)

    # The json field of 'household_numbers' will have a list of household numbers.
    # We need to sort the data with respect to each household number in order to
    # append it in formdict.

    for x in community_mobilization_data_list:
        HH_list_flat=[]
        HH_list_flat.append(json.loads(x['household_number']))
        x['household_number'] = HH_list_flat[0]

    try:
        for i in range(len(community_mobilization_data)):
            y = community_mobilization_data[i]
            for z in y.household_number:
                for x in formdict:
                    if int(x['Household_number']) == int(z):
                        new_activity_type = community_mobilization_data[i].activity_type.name
                        x.update({new_activity_type : y.activity_date_str})
    except Exception as e:
        print e


    vendor = VendorHouseholdInvoiceDetail.objects.filter(slum__shelter_slum_code = 273425265502)
    # Arranging name_label_data with respect to label and corresponding codes('names' is the key used for them in the json) and labels
    name_label_data_dict={obj_name_label_data['name'] : {child['name']:child['label'] for child in obj_name_label_data['children']} for obj_name_label_data in name_label_data}

    for y in vendor:
        print y.vendor.vendor_type.name
        for z in y.household_number:
            for x in formdict:
                if int(x['Household_number']) == int(z):

                    vendor_name = "vendor_type"+y.vendor.vendor_type.name
                    invoice_number =  "invoice_number"+y.vendor.vendor_type.name
                    x.update({
                        vendor_name : y.vendor.name,
                        invoice_number : y.invoice_number
                    })

                # Changing the codes to actual labels
                try:
                    for key_f in x:
                        for key_nl in name_label_data_dict.keys():
                            if str(key_nl) in str(key_f):
                                string = x[key_f].split(" ")
                                for num in string:
                                    string[string.index(num)] = name_label_data_dict[key_nl][num]
                                x[key_f] = ", ".join(string)
                except Exception as e:
                    print e
    return HttpResponse(json.dumps(formdict),  content_type = "application/json")



def trav(node):
    #Traverse uptill the child node and add to list
    if 'type' in node and node['type'] == "group":
        return list(chain.from_iterable([trav(child) for child in node['children']]))
    elif (node['type'] == "select one" or node['type'] == "select all that apply") and 'children' in node.keys():
        return [node]
    return []




def define_columns(request):
    formdict_new = [
        {"data": "Household_number", "title": "Household Number"},
        {"data": "Date_of_survey", "title": "Date of Survey"},
        {"data": "Name_s_of_the_surveyor_s", "title": "Name of the Surveyor"},
        {"data": "Type_of_structure_occupancy", "title": "Type of structure occupancy"},
        {"data": "Type_of_unoccupied_house", "title": "Type of unoccupied house"},
        {"data": "Parent_household_number", "title": "Parent household number"},
        {"data": "group_og5bx85/Full_name_of_the_head_of_the_household",
         "title": "Full name of the head of the household"},
        {"data": "group_og5bx85/Type_of_survey", "title": "Type of the survey"},
        {"data": "group_el9cl08/Enter_the_10_digit_mobile_number", "title": "Mobile number"},
        {"data": "group_el9cl08/Aadhar_number", "title": "Aadhar card number"},
        {"data": "group_el9cl08/Number_of_household_members", "title": "Number of household members"},
        {"data": "group_el9cl08/Do_you_have_any_girl_child_chi",
         "title": "Do you have any girl child/children under the age of 18?"},
        {"data": "group_el9cl08/How_many", "title": "How many?"},
        {"data": "group_el9cl08/Type_of_structure_of_the_house", "title": "Type of structure of the house"},
        {"data": "group_el9cl08/Ownership_status_of_the_house", "title": "Ownership status of the house"},
        {"data": "group_el9cl08/House_area_in_sq_ft", "title": "House area in sq. ft."},
        {"data": "group_el9cl08/Type_of_water_connection", "title": "Type of water connection"},
        {"data": "group_el9cl08/Facility_of_solid_waste_collection", "title": "Facility of solid waste management"},
        {"data": "group_el9cl08/Does_any_household_m_n_skills_given_below",
         "title": "Does any household member have any of the construction skills give below?"},

        {"data": "group_oi8ts04/Have_you_applied_for_individua",
         "title": "Have you applied for an individual toilet under SBM?"},
        {"data": "group_oi8ts04/How_many_installments_have_you", "title": "How many installments have you received?"},
        {"data": "group_oi8ts04/When_did_you_receive_ur_first_installment",
         "title": "When did you receive your first installment?"},
        {"data": "group_oi8ts04/When_did_you_receive_r_second_installment",
         "title": "When did you receive your second installment?"},
        {"data": "group_oi8ts04/When_did_you_receive_ur_third_installment",
         "title": "When did you receive your third installment?"},
        {"data": "group_oi8ts04/If_built_by_contract_ow_satisfied_are_you",
         "title": "If built by a contractor, how satisfied are you?"},
        {"data": "group_oi8ts04/Status_of_toilet_under_SBM", "title": "Status of toilet under SBM?"},
        {"data": "group_oi8ts04/What_was_the_cost_in_to_build_the_toilet",
         "title": "What was the cost incurred to build the toilet?"},
        {"data": "group_oi8ts04/C1", "title": "Current place of defecation1"},
        {"data": "group_oi8ts04/C2", "title": "Current place of defecation2"},
        {"data": "group_oi8ts04/C3", "title": "Current place of defecation_no SBM"},
        {"data": "group_oi8ts04/C4", "title": "Current place of defecation_3 status of SBM"},
        {"data": "group_oi8ts04/C5", "title": "Current place of defecation_yet to start SBM"},
        {"data": "group_oi8ts04/Is_there_availabilit_onnect_to_the_toilets",
         "title": "Is there availability of drainage to connect to the toilet?"},
        {"data": "group_oi8ts04/Are_you_interested_in_an_indiv",
         "title": "Are you interested in an individual toilet?"},
        {"data": "group_oi8ts04/What_kind_of_toilet_would_you_likes", "title": "What kind of toilet would you like?"},
        {"data": "group_oi8ts04/Under_what_scheme_wo_r_toilet_to_be_built",
         "title": "Under what scheme would you like your toilet to be built?"},
        {"data": "group_oi8ts04/If_yes_why", "title": "If yes, why?"},
        {"data": "group_oi8ts04/If_no_why", "title": "If no, why?"},
        {"data": "group_oi8ts04/What_is_the_toilet_connected_to", "title": "What is the toilet connected to?"},
        {"data": "group_oi8ts04/Who_all_use_toilets_in_the_hou", "title": "Who all use toilets in the household?"},
        {"data": "group_oi8ts04/Reason_for_not_using_toilet", "title": "Reason for not using toilet"},

        {"data": "OnfieldFactsheet", "title": "Factsheet onfield"},
        {"data": "group_ne3ao98/Have_you_upgraded_yo_ng_individual_toilet",
         "title": "Have you upgraded your toilet/bathroom/house while constructing individual toilet?"},
        {"data": "group_ne3ao98/Cost_of_upgradation_in_Rs", "title": "House renovation cost"},
        {"data": "group_ne3ao98/Where_the_individual_ilet_is_connected_to",
         "title": "Where the individual toilet is connected to?"},
        {"data": "group_ne3ao98/Use_of_toilet", "title": "Use of toilet"},

        {"data": "name", "title": "SBM Applicant Name"},
        {"data": "application_id", "title": "Application ID"},
        {"data": "photo_uploaded", "title": "Is toilet photo uploaded on site?"},

        {"data": "agreement_date_str", "title": "Date of Agreement"},
        {"data": "agreement_cancelled", "title": "Agreement Cancelled?"},
        {"data": "septic_tank_date_str", "title": "Date of septic tank supplied"},
        {"data": "phase_one_material_date_str", "title": "Date of first phase material"},
        {"data": "phase_two_material_date_str", "title": "Date of second phase material"},
        {"data": "phase_three_material_date_str", "title": "Date of third phase material"},
        {"data": "completion_date_str", "title": "Construction Completion Date"},
        {"data": "material_shifted_to", "title": "Material sifted to"},

        # Append community mobilization here #

        # Append vendor type here #
    ]

    # We define the columns for community mobilization and vendor details in a dynamic way. The
    # reason being these columns are prone to updates and additions.

    activity_type_model = ActivityType.objects.all()

    try:
        for i in range(len(activity_type_model)):
            formdict_new.append({"data":activity_type_model[i].name, "title":activity_type_model[i].name})
    except Exception as e:
        print e

    vendor_type_model = VendorType.objects.all()

    try:
        for i in vendor_type_model:
            formdict_new.append({"data":"vendor_type"+str(i.name), "title":"Name of "+str(i.name)+" vendor"})
            formdict_new.append({"data":"invoice_number"+str(i.name), "title":str(i.name) + " Invoice Number"})
    except Exception as e:
        print e


    return HttpResponse(json.dumps(formdict_new),  content_type = "application/json")



# As the columns are defined dynamically, the buttons for hiding and showing the coluns should
# also be defined dynamically. The columns fetched for displaying data from Kobo toolbox
# are static. Hence we use their column numbers for adding columns dynamically.
def define_buttons(request):
    activity_type_model = ActivityType.objects.all()
    vendor_type_model = VendorType.objects.all()
    buttons = {}
    buttons['daily_reporting'] = len(activity_type_model)
    buttons['accounts'] = 2 * len(vendor_type_model)
    return HttpResponse(json.dumps(buttons), content_type = "application/json")


def renderMastersheet(request):
    print "########### In renderMastersheet ###########"
    slum_search_field = find_slum()
    return render(request, 'masterSheet.html', {'form': slum_search_field})













