import argparse

from copy import deepcopy
from distutils.util import strtobool
from typing import Dict, Union
from torch import nn

from graphs.dataset import Dataset
from graphs.createAttributeSum import create_sum_map
from helpers.results import Results
from helpers import timing
from helpers.checks import do_checks
from model.embeddingTricks import stack_embeddings, sum_embeddings, concat_embeddings
from model.layers import Emb_Layers, Emb_MLP_Layers, Emb_ATT_Layers
from model.modelTrainer import Trainer

"""This file executes experiments to scale RGCN training with summary graphs. 
After training on summary graphs, the weights and node embeddings of 
the summary model will be transferd to a new model for training on the 
full original graph.
"""

def run_expirements(configs: Dict[str, Union[bool, str, int, float]], 
                    experiments: Dict[str, Dict[str, nn.Module]], 
                    org_path: str, 
                    sum_path: str, 
                    map_path: str) -> None:

    # before running program, do some check and assert or adjust configs if needed
    configs, sum_files = do_checks(configs, sum_path, map_path)

    results = Results()

    experiment_names = [configs['exp']]
    if configs['exp'] == None:
        experiment_names = ['summation', 'mlp', 'attention']

    # create attribute summaries if needed
    if configs['create_attr_sum']:
        timing.log('Creating graph summaries...')
        create_sum_map(org_path, sum_path, map_path, dataset)
        timing.log('Attribtue summaries done')
    
    # initialzie the data and use deepcopy when using data to keep original data unchanged.
    timing.log('Making Graph data...')
    data = Dataset(org_path, sum_path, map_path)
    data.init_dataset()

    for j in range(configs['i']):
    
        # run experiment(s)
        trainer = Trainer(deepcopy(data), configs['hl'], configs['epochs'], configs['emb'], configs['lr'], weight_d=0.00005)
        trainer.train_summaries(configs)
        for exp in experiment_names:
            exp_settings = experiments[exp]
            results.add_key(exp)
            timing.log(f'Start {exp} Experiment')
            results_acc, results_loss, results_f1_w, results_f1_m, test_acc, test_micro, test_macro, orgModel = trainer.train_original(exp_settings['org_layers'], exp_settings['embedding_trick'], configs, exp)
            
            for result in [results_acc, results_loss, results_f1_w, results_f1_m]:
                results.update_run_results(result, exp)

            results.test_accs[f'Test acc {exp}'].append(test_acc)
            results.test_f1_weighted[f'Test F1 weighted {exp}'].append(test_micro)
            results.test_f1_macro[f'Test F1 macro {exp}'].append(test_macro) 

            timing.log(f'{exp} experiment done')
            results.print_trainable_parameters(orgModel, exp, trainer)
    configs['sum files'] = sum_files
    results.process_results(configs)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description='experiment arguments')
    parser.add_argument('-dataset', type=str, choices=['AIFB', 'BGS', 'MUTAG', 'AM', 'TEST'], help='inidcate dataset name', default='AIFB')
    parser.add_argument('-sum', type=str, choices=['attr', 'bisim', 'mix', 'dummy', 'one'], default='attr', help='summarization technique')
    parser.add_argument('-exp', type=str, choices=['summation', 'mlp', 'attention', 'baseline'], help='select experiment')
    parser.add_argument('-epochs', type=int, default=51, help='indicate number of training epochs')
    parser.add_argument('-emb', type=int, default=63, help='Node embediding dimension')
    parser.add_argument('-i', type=int, default=1, help='experiment iterations')
    parser.add_argument('-lr', type=float, default=0.01, help='learning rate')
    parser.add_argument('-hl', type=int, default=16, help='hidden layer size')
    parser.add_argument('-e_trans', type=lambda x:bool(strtobool(x)), default=True, help='embedding transfer True/False')
    parser.add_argument('-e_freeze', type=lambda z:bool(strtobool(z)), default=True, help='freeze emebdding after summary training True/False')
    parser.add_argument('-w_trans', type=lambda y:bool(strtobool(y)), default=True, help='RGCN weight transfer True/False')
    parser.add_argument('-w_grad', type=lambda g:bool(strtobool(g)), default=True, help='Weight grad after transfer True/False')
    parser.add_argument('-e_viz', type=lambda h:bool(strtobool(h)), default=False, help='viz embedding tensor')
    parser.add_argument('-create_attr_sum', type=lambda w:bool(strtobool(w)), default=False, help='create attribute summaries before conducting the experiments')
    
    configs = vars(parser.parse_args())

    experiments = {'summation': {'org_layers': Emb_Layers, 'embedding_trick': sum_embeddings},
                    'mlp': {'org_layers': Emb_MLP_Layers, 'embedding_trick': concat_embeddings},
                    'attention': {'org_layers': Emb_ATT_Layers, 'embedding_trick': stack_embeddings},
                    'baseline':{'org_layers': Emb_Layers, 'embedding_trick': None}}

    dataset = configs['dataset']
    sum = configs['sum']
    path = f'graphs/{dataset}/{dataset}_complete.nt'
    sum_path = f'graphs/{dataset}/{sum}/sum/'
    map_path = f'graphs/{dataset}/{sum}/map/'

    run_expirements(configs, experiments, path, sum_path, map_path)
