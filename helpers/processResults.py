import json
import matplotlib.pyplot as plt
import numpy as np

from collections import defaultdict
from datetime import datetime
from typing import Dict, List
from torch import nn


def create_run_report(metric: str, configs: dict, dataset: str, exp: str, i: int, 
                        results_dict: Dict[str, List[float]],  
                        test_results: Dict[str, List[float]]) -> None:
    "wiht this function we save and print important statsitics of the experiment(s)"

    results_collection = defaultdict(dict)
    results_collection.update(configs)
    for experiment, results in results_dict.items():
        exp_strip = experiment.replace(' Accuracy', '')
        max_acc = max(results[0])
        epoch = int(results[0].index(max_acc)) - 1 
        max_acc = max_acc*100
        print(f'{exp_strip.upper()}: After epoch {epoch}, Max accuracy {round(max_acc, 2)}%')
        results_collection[experiment] = {'epoch': epoch, 'acc': max_acc}
    
    for experiment, results in test_results.items():
        avg  = float(sum(results)/len(results))
        std = float(np.std(np.array(results)))
        results_collection[experiment] = {'mean': avg, 'std': std}

    dt = datetime.now()
    str_date = dt.strftime('%d%B%Y-%H%M%S')
    with open(f'./results/{dataset}_{metric}_i={i}_{exp}_{str_date}.json', 'w') as write_file:
            json.dump(results_collection, write_file, indent=4)

def plot_results(metric: str, dataset: str, exp: str, epochs: int, i: int,  results_dict: Dict[str, List[int]]):
    epoch_list = [j for j in range(epochs)]
    for key, result in results_dict.items():
        y = result[0]
        y1 = result[1]
        y2 = result[2]
        x = epoch_list 
        plt.fill_between(x, y1, y2, interpolate=True, alpha=0.35)
        plt.plot(x, y, label = key)

    plt.title(f'{metric} on {dataset} dataset during training epochs')
    plt.xlabel('Epochs')
    plt.ylabel(f'{metric}')
    plt.grid(color='b', linestyle='-', linewidth=0.1)
    plt.margins(x=0)
    plt.legend(loc='best')
    plt.xticks(np.arange(0, len(epoch_list), 5))
    plt.xlim(xmin=0)
    plt.yticks(np.arange(0, 1.1, 0.1))
    plt.ylim(ymin=0)
    dt = datetime.now()
    str_date = dt.strftime('%d%B%Y-%H%M%S')
    plt.savefig(f'./results/{dataset}_{metric}_i={i}_{exp}_{str_date}.pdf', format='pdf')
    plt.show()

def save_to_json(metric: str, dataset: str, exp: str, i: int, results_dict: Dict[str, List[int]]) -> None:
    dt = datetime.now()
    str_date = dt.strftime('%d%B%Y-%H%M%S')
    with open(f'./results/{dataset}_{metric}_i={i}_{exp}_{str_date}.json', 'w') as write_file:
            json.dump(results_dict, write_file, indent=4)

def print_trainable_parameters(model: nn.Module, exp: str) -> int:
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f'number of trainable parameters for {exp.upper()} model: {trainable_params}')
    return trainable_params

def add_data(list1: List[int], list2: List[int]):
    temp_list = list(zip(list1, list2))
    return [x+y for x,y in temp_list]

def get_av_results_dict(i: int, dicts_list: List[Dict[str, int]]) -> Dict[str, List[List]]:
    av_results_dict = defaultdict(list)
    for key in dicts_list[0].keys():
        list_with_lists = [[] for i in range(len(dicts_list[0][key]))]
        # new_lst = [0 for i in range(0, len(dicts_list[0][key]))]
        for dict in dicts_list:
            for i, flt in enumerate(dict[key]):
                list_with_lists[i].append(flt)
        array = np.array(list_with_lists)
        av_results_dict[key].append(list(np.mean(array, axis=1)))
        av_results_dict[key].append(list(np.mean(array, axis=1) - np.std(array, axis=1)))
        av_results_dict[key].append(list(np.mean(array, axis=1) + np.std(array, axis=1)))
    return av_results_dict
    