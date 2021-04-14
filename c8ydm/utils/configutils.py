#!/usr/bin/env python
# -*- coding: utf-8 -*-
import configparser
from configparser import NoOptionError, NoSectionError

class Configuration():
  credentialsCategory = 'secret'
  bootstrapTenant = 'c8y.bootstrap.tenant'
  bootstrapUser = 'c8y.bootstrap.user'
  bootstrapPassword = 'c8y.bootstrap.password'
  tenant = 'c8y.tenant'
  user = 'c8y.username'
  password = 'c8y.password'

  def __init__(self, path):
    self.configPath = path + '/agent.ini'
    self.configuration = configparser.ConfigParser()
    self.readFromFile()

  def readFromFile(self):
    self.configuration.read(self.configPath)

  def getValue(self, category, key):
    try:
      return self.configuration.get(category, key)
    except (NoOptionError, NoSectionError):
      return None

  def setValue(self, category, key, value):
    if category not in self.configuration.sections():
      self.configuration.add_section(category)
    self.configuration.set(category, key, value)
    with open(self.configPath, 'w') as cfgfile:
      self.configuration.write(cfgfile)

  def getBootstrapCredentials(self):
    tenant = self.getValue(self.credentialsCategory, self.bootstrapTenant)
    user = self.getValue(self.credentialsCategory, self.bootstrapUser)
    password = self.getValue(self.credentialsCategory, self.bootstrapPassword)

    if tenant is not None and user is not None and password is not None:
      return [tenant, user, password]
    return None

  def getCredentials(self):
    tenant = self.getValue(self.credentialsCategory, self.tenant)
    user = self.getValue(self.credentialsCategory, self.user)
    # if the password contains % it needs to be escaped as % has special meaning in configparser
    password = self.getValue(self.credentialsCategory, self.password.replace('%','%%'))

    if tenant is not None and user is not None and password is not None:
      return [tenant, user, password]
    return None

  def writeCredentials(self, tenant, user, password):
    self.configuration.set(self.credentialsCategory, self.tenant, tenant)
    self.configuration.set(self.credentialsCategory, self.user, user)
    self.configuration.set(self.credentialsCategory, self.password, password.replace('%', '%%'))
    with open(self.configPath, 'w') as cfgfile:
      self.configuration.write(cfgfile)

  def getConfigString(self):
    configs = []
    for section in self.configuration.sections():
      if section == 'secret':
        continue
      for (key, val) in self.configuration.items(section):
        configs.append(section + '.' + key + '=' + val)
    return '\n'.join(configs)

  def writeConfigString(self, configString):
    configLines = configString.split('\n')
    newConfiguration = configparser.ConfigParser()
    newConfiguration.add_section('secret')
    for (key, val) in self.configuration.items('secret'):
      newConfiguration.set('secret', key, val.replace('%', '%%'))
    for configLine in configLines:
      splitted = configLine.split('.', 1)
      section = splitted[0]
      if section == 'secret':
        continue
      splitted = splitted[1].split('=', 1)
      key = splitted[0]
      value = splitted[1]
      if not newConfiguration.has_section(section):
        newConfiguration.add_section(section)
      newConfiguration.set(section, key, value)
    with open(self.configPath, 'w') as cfgfile:
      newConfiguration.write(cfgfile)
    self.configuration = newConfiguration
