

def main():
    functions = [auditMode,auditStockroom,findThing,findUser,bulkArchive,
      bulkCloneOffUmass,bulkCloneOnUmass,bulkStudentSignout]
    for i,f in enumerate(functions):
        print(f"{i}) {f.__name__}")
    print(f"{len(functions)}) exit")
    choice = int(input("choice: "))
    while choice<0 or choice> len(functions):
        print("that choice in unavailable")
        choice = int(input("choice: "))
    if int(choice) == len(functions):
      return
    try:
        functions[choice]()
    except KeyboardInterrupt:
        pass
    
if __name__ =="__main__":
 from dotenv import load_dotenv
 load_dotenv('.env')
 from apiMenu import *
 from barManual import *
 from AssetControl import *
 main()
