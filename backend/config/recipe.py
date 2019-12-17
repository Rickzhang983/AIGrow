#!/usr/bin/env python
# -*- coding:utf-8 -*-
import json, datetime

recipeCache = {}

class Phase():
    def __init__(self, name, duration, factor_values):
        self.name = name
        self.duration = duration
        self.factors = factor_values
        #print ("phase %s added, duration %d"%(name,duration))

    @staticmethod
    def from_json(name,obj):
        v = obj.items()
        duration = 0 #in minutes
        factors={}
        for k,val in v:
            if k == "hours": duration += val*60
            elif k == "minutes": duration += val
            else:
                factors[k]=val
        return Phase (name,duration, factors)

    def to_json(self):
        return self.__dict__

    def __iter__(self):
        for k, v in self.__dict__.items():
            if k=="factors":
                yield {k,json.dumps(v,ensure_ascii=False)}
            else:
                yield {k,v}

    def totalDuration(self):
        return self.duration

class Stage():
    def __init__(self, name, cycles, phases):
        self.name = name
        self.cycles = cycles
        self.phases = phases
        #print ("stage %s added"%name)

    def __iter__(self):
        for k, v in self.__dict__.items():
            if k!="phases":
                yield (k, v)
            else:
                s=[]
                for v1 in v:
                    s.append (v1.__dict__)
                yield (k,s)

    def totalDuration(self):
        t=0
        for p in self.phases:
           t += p.totalDuration()
        return t*self.cycles

    @staticmethod
    def from_json(obj):
        phases =[]
        for k,v in obj['phases'].items():
            phases.append (Phase.from_json(k,v))
        return Stage(obj['name'],obj['cycles'],phases)

class RecipeTemplate():
    def __init__(self, id, applicables, status, date_created, author, stages,version="1.0"):
        self.id = id
        self.applicables = applicables
        self.status = status
        self.version = version
        self.date_created = date_created
        self.author = author
        self.stages = stages

    def __iter__(self):
           for k, v in self.__dict__.items():
               if k =="stages":
                   s=[]
                   for v1 in v:
                       s.append(dict(v1))
                   yield (k, s)
               else:
                   yield (k, v)


    def totalDuration(self):
        t=0
        for s in self.stages:
           t += s.totalDuration()
        return t

    def to_json(self):
        return dict(self) #json.dumps(dict(self),ensure_ascii=False)

    @staticmethod
    def from_json(obj):
        stages =[]
        for stage in obj['stages']:
            s = Stage.from_json(stage)
            stages.append (s)
        return RecipeTemplate(obj['id'], obj['applicables'], obj['status'], obj["date_created"],obj["author"], stages,obj['version'])

def byteify(input):
    if isinstance(input, dict):
        return {byteify(key):byteify(value) for key,value in input.items()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, str):
        return input
    elif isinstance(input, Stage):
        return input.__dict__


# import os
# if recipeCache == {}:
#     for domain_name in os.listdir("domain"):
#         recipeCache[domain_name]={}
#         try:
#             for file in os.listdir("domain"+os.sep+domain_name+os.sep+"recipes"+os.sep+"*.json"):
#                 with open(file, 'r',encoding='utf-8')as f:
#                     print("loading recipes .....")
#                     js = json.load(f)
#                     print (js)
#                     recipe = RecipeTemplate.from_json(js)
#                     recipeCache[domain_name][recipe.id] = recipe
#                     #print ("Recipe %s has a duration of %d minutes, %d days" %(recipe.id, recipe.totalDuration(),recipe.totalDuration()/60/24))
#                 f.close()
#         except Exception as e:
#             print(e)
# print (recipeCache)

import glob,os
if recipeCache == {}:
    for domain_name in glob.glob1("domain","*"):
        recipeCache[domain_name]={}
        path=os.path.join("domain",domain_name,"recipes")
        #print ("path",path)
        for file in glob.glob1(path,"*.json"):
            try:
                with open(path+os.sep+file, 'r',encoding='utf-8')as f:
                    #print("loading recipes from ", file)
                    js = json.load(f)
                    #print (js)
                    recipe = RecipeTemplate.from_json(js)
                    recipeCache[domain_name][recipe.id] = recipe
                    #print ("Recipe %s has a duration of %d minutes, %d days" %(recipe.id, recipe.totalDuration(),recipe.totalDuration()/60/24))
                f.close()
            except Exception as e:
                print(e)
#print (recipeCache)


class RecipeInstance():
    # start_time is a time.struct_time
    def __init__(self,domain, template_name,start_time, offset_minutes=0):
        try:
            self.template = recipeCache[domain].get(template_name)
            self.start = start_time
            self.offset = offset_minutes
        except Exception as e:
            raise RuntimeError("No template found for domain '%s' or template '%s'"%(domain, template_name))

    def currentState(self):
        import time
        tm = time.localtime()
        dt = datetime.datetime(tm[0],tm[1],tm[2],tm[3],tm[4],tm[5])
        old = datetime.datetime(self.start[0],self.start[1],self.start[2],self.start[3],self.start[4],self.start[5])
        gap = dt -old
        if self.template.status != "active":
            raise RuntimeError("Inactive")
        gap_mins= gap.days*24*60+gap.seconds/60
        if gap_mins <0:
            raise RuntimeError("Standby")
        gap_mins+= self.offset
        if gap_mins >= self.template.totalDuration():
            raise RuntimeError("Finished")
        measure=0
        first_stage=""
        first_phase=""
        last_stage=""
        last_phase=""
        for stage in self.template.stages:
            step = stage.totalDuration()
            measure += step
            if self.offset < measure:
                first_stage = stage.name
            last_stage = stage.name
            if gap_mins > measure:
                # move to next stage
               continue
            else: #move back to phase
                measure -= step
                past_cycles = int((gap_mins-measure)/(step/stage.cycles))
                measure += past_cycles*step/stage.cycles
                # Now locate the specific phase
                for phase in stage.phases:
                    microstep = phase.totalDuration()
                    measure += microstep
                    if self.offset < measure:
                        first_phase = phase.name
                    last_phase = phase
                    if gap_mins > measure:
                        continue
                    else:
                        past_duration = ( gap_mins -measure + microstep)
                        return first_stage, first_phase, last_stage, past_cycles, last_phase,past_duration


def test():
    print ("-----------not started---------")
    try:
        # 还没有开始
        rs = RecipeInstance("hydroponics","general_greens",(2019,7,5,12,35,00),2*24*60)
        #print (rs.template.to_json())
        last_stage, past_cycles, last_phase,past_duration = rs.currentState()
        print("stage %s ; cycles %d ; phase %s ; past  %d minutes after the last phase" % (
            last_stage, past_cycles, last_phase.name, past_duration))
        #开始了，还没有完成
    except Exception as e:
        print(e)
    print ("-----------just start---------")
    try:
        rs = RecipeInstance("hydroponics","general_greens",(2019,6,15,0,00,00),15*24*60)
        current_stage, past_cycles, last_phase,past_duration = rs.currentState()
        print("stage %s ; cycles %d ; phase %s ; past  %d minutes after the last phase" % (
            current_stage, past_cycles, last_phase.name, past_duration))
        result = {"id": rs.template.id, "applicables":rs.template.applicables, "start_time": rs.start,\
                  "offset_hours":rs.offset/60,"current_stage":current_stage,"past_cycles":past_cycles, "latest_phase":last_phase,\
                  "past_duration":past_duration, "remaining":last_phase.duration-past_duration}

        print (result)
        print (rs.template.to_json())
    except Exception as e:
        print(e)

    print("-----------3---------")
        #已经完了
    try:
        rs = RecipeInstance("hydroponics","general_greens",(2019,4,5,7,35,00),2*24*60)
        last_stage, past_cycles, last_phase,past_duration = rs.currentState()
        print("stage %s ; cycles %d ; phase %s ; past  %d minutes after the last phase" % (
            last_stage, past_cycles, last_phase.name, past_duration))
    except Exception as e:
        print(e)


if __name__ == '__main__':
    test()