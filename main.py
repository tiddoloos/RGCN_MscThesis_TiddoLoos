import argparse

from copy import deepcopy
from collections import defaultdict
from typing import Callable, Dict, List

from graphdata.graphData import Dataset
from helpers.processResults import plot_and_save, print_max_result
from helpers import timing
from model.embeddingTricks import stack_embeddings, sum_embeddings, concat_embeddings
from model.models import Emb_Layers, Emb_MLP_Layers, Emb_ATT_Layers, BaseLayers
from model.modelTrainer import Trainer



def initialize_expiremts(args: Dict[str, str], experiments: Dict[str, Dict[str, Callable]]) -> None:
    """This functions executes experiments to scale graph training with RGCN. 
    After training on summary graphs, the weights of and node embeddings of 
    the summary model will be transferd to a new model for training on the 
    original graph. Also a baseline experiment is carried out.
    """

    hidden_l = 16
    epochs = 51
    lr = 0.01
    weight_d = 0.0005
    #embedding dimension must be devisible by the number of summary graphs (attention layer)
    embedding_dimension = 63

    # initialzie the data and use deepcopy to keep original data unchanged.
    data = Dataset(args['dataset'])
    data.init_dataset(embedding_dimension)
    
    if args['exp'] == None:
        results_exp_acc = dict()
        results_exp_loss = dict()
        for exp, exp_settings in experiments.items():
            trainer = Trainer(deepcopy(data), hidden_l, epochs, embedding_dimension, lr, weight_d)
            results_acc, results_loss = trainer.exp_runner(exp_settings['sum_layers'], exp_settings['org_layers'], exp_settings['embedding_trick'], exp_settings['transfer'], exp)
            results_exp_acc.update(results_acc)
            results_exp_loss.update(results_loss)
            timing.log('experiment done')
    
    if args['exp'] != None:
        exp = args['exp']
        exp_settings = experiments[exp]
        trainer = Trainer(deepcopy(data), hidden_l, epochs, embedding_dimension, lr, weight_d)
        results_exp_acc, results_exp_loss = trainer.exp_runner(exp_settings['sum_layers'], exp_settings['org_layers'], exp_settings['embedding_trick'], exp_settings['transfer'], exp)
        timing.log('experiment done')

    # results_baseline_acc = defaultdict(list)
    # results_baseline_loss = defaultdict(list)

    # baseline_data = deepcopy(data)
    # trainer = Trainer(data, hidden_l, epochs, embedding_dimension, lr, weight_d)
    # baselineModel = BaseLayers(embedding_dimension, len(data.orgGraph.relations.keys()), hidden_l, data.num_classes)
    # results_baseline_acc['baseline Accuracy'], results_baseline_loss['baseline Loss'] = trainer.train(baselineModel, baseline_data.orgGraph, sum_graph=False)
    # timing.log('experiment done')

    # results_acc = {**results_exp_acc, **results_baseline_acc}
    # results_loss = {**results_exp_loss, **results_baseline_loss}

    print_max_result(results_acc)
    plot_and_save('Accuracy', args['dataset'], results_acc, epochs, args['exp'])
    plot_and_save('Loss', args['dataset'], results_loss, epochs, args['exp'])


parser = argparse.ArgumentParser(description='experiment arguments')
parser.add_argument('-dataset', type=str, choices=['AIFB', 'MUTAG', 'AM', 'TEST'], help='inidcate dataset name')
parser.add_argument('-exp', type=str, choices=['sum', 'mlp', 'attention', 'embedding'], help='select experiment')
args = vars(parser.parse_args())

experiments = {
'sum': {'sum_layers': Emb_Layers, 'org_layers': Emb_Layers, 'embedding_trick': sum_embeddings, 'transfer': True},
'mlp': {'sum_layers': Emb_Layers, 'org_layers': Emb_MLP_Layers, 'embedding_trick': concat_embeddings, 'transfer': True},
'attention': {'sum_layers': Emb_Layers, 'org_layers': Emb_ATT_Layers, 'embedding_trick': stack_embeddings, 'transfer': True},
'baseline': {'sum_layers': None, 'org_layers': Emb_Layers, 'embedding_trick': None, 'transfer': False}
}


if __name__=='__main__':
    initialize_expiremts(args, experiments)
