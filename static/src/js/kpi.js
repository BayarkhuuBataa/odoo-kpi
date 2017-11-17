function goToLocation(type,data) {
    var prot = window.location.protocol;
    var host = window.location.host;
    window.open(prot +"//" + host +"/report/html/hq_kpi.kpi_report/1?type=" + type + "&data="+data,"_blank");
}