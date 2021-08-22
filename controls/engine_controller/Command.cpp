#include "Command.h"
#include <stdio.h>
#include <string.h>

Command::Command()
{
  this->prefix = "";
  this->data = "";
}

Command::Command(const char* prefix, const char* data)
{
  this->prefix = prefix;
  this->data = data;
}

Command::Command(const char* s, char delim)
{
  char* temp = strdup(s);
  char* delims = &delim;
  char* token = strtok(temp, delims);

  this->prefix = strdup(token);
  this->data = strtok(NULL, delims);

  while(this->data[0] == ' ')
  {
    this->data = &this->data[1];
  }

  /*this->data = &this->data[2];

  size_t len = strlen(this->data);
  this->data = strndup(this->data, len - 1);
  //strncpy(this->data, strdup(this->data), len - 1);*/
}

const char* Command::getPrefix()
{
  return this->prefix;
}

const char* Command::getData()
{
  return this->data;
}
