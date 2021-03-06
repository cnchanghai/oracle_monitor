#coding=utf-8
#coding=gbk
from django.core.management.base import BaseCommand
from oracle.models import oraclelist
from oracle.models import oraclestatus
import os
import redis
import time
import types
from oracle.monitor.getoracleinfo import *
from oracle.monitor.sendmail import *
r=redis.StrictRedis()
nowtime=str(time.time()).split('.')[0]
class Command(BaseCommand):
    def handle(self, *args, **options):
	oraclestatus.objects.all().delete()
        ip=oraclelist.objects.all().order_by('tnsname')
        for i in ip:
	    if i.monitor_type==1:
		    ipaddress1=i.ipaddress
		    username=i.username
		    password=i.password
		    port=i.port
		    tnsname1=i.tnsname
		    try:
			db = cx_Oracle.connect(username+'/'+password+'@'+ipaddress1+':'+port+'/'+tnsname1 ,mode=cx_Oracle.SYSDBA)
		    except Exception , e:
			content= (i.ipaddress+' is Unreachable,The reason is '+str(e)).strip()
			send_mail(to_list,'Oracle Monitor Exception Occured',content)
			print content
			break
		    else:
			cursor = db.cursor()
			jobstatus=checkjob(cursor)
			alertstatus=checkalert(cursor)
			if type(alertstatus) is types.StringType:
			    alertstatus=='normal'
			else:
			    alertstatus='error'
			dbsize=getdbsize(cursor)
			tbstatus=getspace(cursor)
			invalid_object=checkinvalidobject(cursor)
			mv_compile_state=check_mv_compile_states(cursor)
			oracle_info=check_info(cursor)
			sga_size=get_sga_size(cursor)
			segsize=getsegsize(cursor)
			cursor.close()
			db.close()
			if segsize:
				sizekey='SegSize='+ipaddress1+'='+tnsname1
				value=nowtime+':'+str(segsize)
				r.lpush(sizekey,value)
			if oraclestatus.objects.filter(ipaddress=ipaddress1):
			    status=oraclestatus.objects.filter(ipaddress=ipaddress1)
			    status.update(**{'tnsname':tnsname1,'ipaddress':ipaddress1,'jobstatus':jobstatus,'alertstatus':alertstatus,'dbsize':dbsize,'tbstatus':tbstatus,'invalid_object':invalid_object,'mv_compile_state':mv_compile_state,'host_name':oracle_info[0],'version':oracle_info[1],'startup_time':oracle_info[2],'status':oracle_info[3],'archiver':oracle_info[4],'sga_size':sga_size})
			else:
			    createtnsname=oraclestatus(ipaddress=ipaddress1)
			    createtnsname.save()
			    status=oraclestatus.objects.filter(ipaddress=ipaddress1)
			    status.update(**{'tnsname':tnsname1,'ipaddress':ipaddress1,'jobstatus':jobstatus,'alertstatus':alertstatus,'dbsize':dbsize,'tbstatus':tbstatus,'invalid_object':invalid_object,'mv_compile_state':mv_compile_state,'host_name':oracle_info[0],'version':oracle_info[1],'startup_time':oracle_info[2],'status':oracle_info[3],'archiver':oracle_info[4],'sga_size':sga_size})
			
