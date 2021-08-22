#ifndef Command_h
#define Command_h

class Command
{
  public:
    Command();
    Command(const char* prefix, const char* data);
    Command(const char* s, char delimiter);
    const char* getPrefix();
    const char* getData();
  private:
    const char* prefix;
    const char* data;
};

#endif
