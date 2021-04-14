#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging, time, json, time
from c8ydm.framework.modulebase import Listener, Initializer
from c8ydm.framework.smartrest import SmartRESTMessage
import apt


class SoftwareManager(Listener, Initializer):

    def group(self, seq, sep):
        result = [[]]
        for e in seq:
            #logging.info("e: "+str(e) +" sep: " + str(sep))
            if sep not in str(e):
                result[-1].append(e)
            else:
                result[-1].append(e[:e.find(sep)])
                result.append([])

        if result[-1] == []:
            result.pop() # thx iBug's comment
        return result

    def handleOperation(self, message):
        try:
            if 's/ds' in message.topic and message.messageId == '516':
                ## When multiple operations received just take the first one for further processing
                logging.info("message received :" + str(message.values))
                messages = self.group(message.values, '\n')[0]
                logging.info("message processed:" + str(messages))
                deviceId = messages.pop(0)
                logging.info('Software update for device ' + deviceId + ' with message ' + str(messages))
                executing = SmartRESTMessage('s/us', '501', ['c8y_SoftwareList'])
                self.agent.publishMessage(executing)
                softwareToInstall = [messages[x:x + 3] for x in range(0, len(messages), 3)]
                errors = self.installSoftware(softwareToInstall, False)
                logging.info('Finished all software update')
                if len(errors) == 0:
                    # finished without errors
                    finished = SmartRESTMessage('s/us', '503', ['c8y_SoftwareList'])
                else:
                    # finished with errors
                    finished = SmartRESTMessage('s/us', '502', ['c8y_SoftwareList', ' - '.join(errors)])
                self.agent.publishMessage(finished)
                self.agent.publishMessage(self.getInstalledSoftware(False))
        except Exception as e:
          logging.exception(e)
          failed = SmartRESTMessage('s/us', '502', ['c8y_SoftwareList', str(e)])
          self.agent.publishMessage(failed)


    def getSupportedOperations(self):
        return ['c8y_SoftwareList']


    def getSupportedTemplates(self):
        return []

    def getMessages(self):
        installedSoftware = self.getInstalledSoftware(True)
        return [installedSoftware]

    def getInstalledSoftware(self, with_update):
        allInstalled = []

        cache = apt.cache.Cache()
        if with_update:
            logging.info('Starting apt update....')
            cache.update()
            logging.info('apt update finished!')
        cache.open()

        for pkg in cache:
            if (pkg.is_installed and not pkg.shortname.startswith('lib')):
                allInstalled.append(pkg.shortname)
                allInstalled.append(pkg.installed.version)
                allInstalled.append('')
        
        cache.close()

        return SmartRESTMessage('s/us', '116', allInstalled)


    def getFormatedSnaps(self):

        allInstalled = {}

        return allInstalled

    def installSoftware(self, toBeInstalled, with_update):
        cache = apt.cache.Cache()
        if with_update:
            logging.info('Starting apt update....')
            cache.update()
            logging.info('apt update finished!')
        cache.open()

        for software in toBeInstalled:
            pkg = cache[software[0]]
            # Software currently installed in the same version
            if pkg.is_installed and pkg.installed.version == software[1]:
                # no action needed
                logging.debug('existing ' + pkg.shortname + '=' + pkg.installed.version)
            else:
                logging.info('install ' + pkg.shortname + '=' + software[1])
                candidate = pkg.versions.get(software[1])
                pkg.candidate = candidate
                pkg.mark_install()

        # Check what needs to be uninstalled
        toBeInstalledSoftware = [i[0] for i in toBeInstalled]
        for pkg in cache:
            if not pkg.shortname.startswith('lib') and pkg.is_installed and pkg.shortname not in toBeInstalledSoftware:
                logging.info('delete ' + pkg.shortname + '=' + pkg.installed.version)
                pkg.mark_delete()

        try:
            logging.info('Starting apt install/removal of Software..')
            cache.commit()
            logging.info("Install/Removal of Software finished!")
        except Exception as e:
            logging.error(e)

        return []
