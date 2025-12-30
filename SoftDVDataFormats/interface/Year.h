#ifndef SoftDVDataFormats_Year_h
#define SoftDVDataFormats_Year_h

namespace SoftDV {

    std::pair<std::string,std::string> getEra(double run_number) {
        std::vector<int> runs({352319, 355065, 355794, 357487, 359022, 360332, 362350, 367080, 369803, 378981});
        //std::vector<std::string> eras({"2022A","2022B","2022C","2022D","2022E","2022F","2022G","2023C","2023D","2024"});
        std::vector<std::pair<std::string,std::string>> eras = {
            {"2022Pre","Era2022A"}, //352319
            {"2022Pre","Era2022B"}, //355065
            {"2022Pre","Era2022C"}, //355794
            {"2022Pre","Era2022D"}, //357487
            {"2022Post","Era2022E"}, //359022
            {"2022Post","Era2022F"}, //360332
            {"2022Post","Era2022G"}, //362350
            {"2023Pre","Era2023PreAll"}, //367080
            {"2023Post","Era2023PostAll"}, //369803
            {"2024","Era2024All"} //378981
        };
        auto pos = std::upper_bound(runs.begin(),runs.end(),run_number)-runs.begin()-1;
        if (pos<0){
            return std::pair<std::string,std::string>({"NA","NA"});
        }
        if (pos>(runs.size()-1)){
            throw cms::Exception("Year", "Run number out of run ranges!");
        }
        return eras[pos];

    }
}

#endif
