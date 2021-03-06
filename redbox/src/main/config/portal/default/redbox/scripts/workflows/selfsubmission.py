import time
from com.googlecode.fascinator.common import JsonSimple
from com.googlecode.fascinator.api.storage import StorageException
from java.io import ByteArrayInputStream
from java.lang import String
from org.apache.commons.lang import StringEscapeUtils


def truncate(s, maxLength):
    return s[:maxLength] + (s[maxLength:] and "...")

class SelfsubmissionData:
    def __activate__(self, context):
        self.__services = context["Services"]
        self.__formData = context["formData"]
        self.log = context["log"]
        self.__auth = context["page"].authentication
        self.__oid = self.__formData.get("oid")
        self.__object = self.__getObject()
        self.__errorMessage = None
        self.packagePid = None
        self.__tfpackage = None

        pidList = self.__object.getPayloadIdList()
        for pid in pidList:
            if pid.endswith(".tfpackage"):
                self.packagePid = pid
        self.__requestData = self.__getJsonData(self.packagePid)
        self.__workflowData = self.__getJsonData("workflow.metadata")

        #print " ***** formData:", self.__formData
        #print " ***** requestData:", self.__requestData
        #print " ***** workflowData:", self.__workflowData

        if self.__formData.get("func") == "update-package-meta-deposit":
            result = self.__update(True)
            writer = context["response"].getPrintWriter("application/json; charset=UTF-8")
            writer.println(result)
            writer.close()
        elif self.__formData.get("func") == "update-package-meta-deposit-save":
            result = self.__update(False)
            writer = context["response"].getPrintWriter("application/json; charset=UTF-8")
            writer.println(result)
            writer.close()
        if self.__errorMessage:
            print "Error: %s" % self.__errorMessage
            
            
        ### Supports form rendering, not involved in AJAX
    def getJsonMetadata(self):
        package = self._getTFPackage()
        ## Look for a title
        title = package.getString("", ["dc:title"])
        title = package.getString(title, ["title"])
        ## And a description
        description = package.getString("", ["dc:abstract"])
        description = package.getString(description, ["description"])
        ## Make sure we have the fields we need
        json = package.getJsonObject()
        json.put("dc:title", title)
        json.put("dc:abstract", description)
        ## fix newlines
        ignoreFields = ["metaList", "relationships", "responses"]
        for key in json:
            if key not in ignoreFields:
                value = json.get(key)
                if value and value.find("\n"):
                    value = value.replace("\n", "\\n")
                    json.put(key, value)
                    ##self.log.info("****** %s=%s" % (key,value))
        jsonStr = package.toString(True)
        return jsonStr

    def _getTFPackage(self):
        if self.__tfpackage is None:
            payload = None
            inStream = None

            # We don't need to worry about close() calls here
            try:
                object = self.__getObject()
                sourceId = object.getSourceId()
                
                payload = None
                if sourceId is None or not sourceId.endswith(".tfpackage"):
                    # The package is not the source... look for it
                    for pid in object.getPayloadIdList():
                        if pid.endswith(".tfpackage"):
                            payload = object.getPayload(pid)
                            payload.setType(PayloadType.Source)
                else:
                    payload = object.getPayload(sourceId)
                inStream = payload.open()
            
            except Exception, e:
                self.log.error("Error during package access", e)
                return None

            # The input stream has now been opened, it MUST be closed
            try:
                self.__tfpackage = JsonSimple(inStream)
            except Exception, e:
                self.log.error("Error parsing package contents", e)
            payload.close()
            
        return self.__tfpackage

    def getFormData(self, field):
        return StringEscapeUtils.escapeHtml(self.__formData.get(field, ""))

    def getRequestData(self, field):
        return StringEscapeUtils.escapeHtml(self.__requestData.getString("", [field]))

    def getOid(self):
        return self.__oid

    def getCurrentStep(self):
        return self.__workflowData.getString(None, ["step"])

    def isSubmitted(self):
        return self.__requestData.getBoolean(False, ["redbox:submissionProcess.redbox:submitted"])

    def getErrorMessage(self):
        return self.__errorMessage
    
    def getSubmitDate(self):
        return time.strftime("%Y-%m-%d %I:%M:%S %p")

    def __getJsonData(self, pid):
        data = None
        object = self.__getObject()
        payload = object.getPayload(pid)
        data = JsonSimple(payload.open())
        payload.close()
        return data

    def __getWorkflow(self, ):
        if self.__getObject() and self.__workflow is None:
            try:
                wfPayload = self.__object.getPayload("workflow.metadata")
                self.__workflow = JsonSimple(wfPayload.open())
                wfPayload.close()
            except StorageException, e:
                self.__errorMessage = "Failed to retrieve workflow metadata: " + e.getMessage()
        return self.__workflow

    def __getObject(self):
        obj = None
        try:
            obj = self.__services.storage.getObject(self.__oid)
        except StorageException, e:
            self.__errorMessage = "Failed to retrieve object: " + e.getMessage()
            return None
        return obj

    def __update(self, advanceWorkflow):
        print "Updating '%s'" % self.__oid
        result = '{"ok":"Updated OK"}'

        if self.__formData.get("acceptOnly", "false") == "false":
            # update from form data
            data = self.__requestData.getJsonObject()
            formFields = self.__formData.getFormFields()
            for formField in formFields:
                if formField == "metaList" :
                    metaList = list(self.__formData.getValues("metaList"))
                    data.put(formField, metaList)
                else :
                     data.put(formField, self.__formData.get(formField))
                
            description = self.__formData.get("dc:description", "[No description]")
            submitTitle = self.__formData.get("dc:title", None)
            if submitTitle:
                data.put("title", submitTitle)
            else:
                #data.put("title", truncate(description, 25))
                data.put("title", description)
            self.__updatePayload(self.packagePid, data)

        # update workflow metadata
        if self.__auth.is_logged_in():
            if advanceWorkflow:
                wf = self.__workflowData.getJsonObject()
                wf.put("step", "investigation")
                wf.put("label", "Investigation")
                wf.put("pageTitle", "Describe my data")
                self.__updatePayload("workflow.metadata", wf)
                # update ownership to the one who accepted the submission
                self.__object.getMetadata().setProperty("owner", self.__auth.get_username())
        else:
            # update ownership so guest users cannot see submission requests
            self.__object.getMetadata().setProperty("owner", "system")
        self.__object.close();

        self.__services.indexer.index(self.__oid)
        self.__services.indexer.commit()
        return result

    def __updatePayload(self, pid, data):
        jsonString = String(data.toString())
        jsonData = jsonString.getBytes("UTF-8")
        self.__object.updatePayload(pid, ByteArrayInputStream(jsonData))
