'''
Created on 2012-02-08

@author: Andrew Roth
'''
from collections import OrderedDict

from pyclone.model import DataPoint, BinomialLikelihood
from pyclone.post_process import DpSamplerPostProcessor
from pyclone.results import SamplerResults
from pyclone.samplers import DirichletProcessSampler

import csv
import os

def run_dp_model(args):
    '''
    Run a fresh instance of the DP model.
    '''
    if not os.path.exists(args.out_dir):
        os.makedirs(args.out_dir)
    
    data = load_data(args.in_file_name)
    
    results_file_prefix = os.path.join(args.out_dir, "results")
    
    results = SamplerResults(results_file_prefix)
    
    results['input_file'] = args.in_file_name
    
    results['genes'] = data.keys()
    
    likelihoods = [BinomialLikelihood(data_point) for data_point in data]
    
    sampler = DirichletProcessSampler(likelihoods, burnin=args.burnin, thin=args.thin)
    
    sampler.sample(results, num_iters=args.num_iters)
    
    results['sampler'] = sampler
    
    results.close()

def restart_dp_model(args):
    '''
    Restart an existing analysis.
    '''
    if not os.path.exists(args.out_dir):
        raise Exception("{0} does not exist.".format(args.out_dir))
    
    results_file_prefix = os.path.join(args.out_dir, "results")
    
    results = SamplerResults(results_file_prefix)
    
    sampler = results['sampler']
    
    sampler.restart(results, num_iters=args.num_iters)
    
    results.close()

def load_data(input_file_name):
    '''
    Load data from PyClone formatted input file.
    '''
    data = OrderedDict()
    
    reader = csv.DictReader(open(input_file_name), delimiter='\t')

    for row in reader:
        gene = row['gene']
        
        a = int(row['a'])
        
        d = int(row['d'])
        
        mu_r = [float(x) for x in row['mu_r'].split(',')]
        delta_r = [float(x) for x in row['delta_r'].split(',')]
        
        mu_v = [float(x) for x in row['mu_v'].split(',')]
        delta_v = [float(x) for x in row['delta_v'].split(',')]
        
        data[gene] = DataPoint(a, d, mu_r, mu_v, delta_r, delta_v)

    return data
        
def write_results(results_db, out_dir):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    
    post_processor = DpSamplerPostProcessor(results_db)
    
    # Save genes
    gene_file = os.path.join(out_dir, "genes.tsv")
    writer = csv.writer(open(gene_file, 'w'), delimiter='\t')
    writer.writerows(list_to_csv_rows(post_processor.genes))
    
    # Save alpha
    alpha_file = os.path.join(out_dir, 'alpha.tsv')
    writer = csv.writer(open(alpha_file, 'w'), delimiter='\t')
    writer.writerows(list_to_csv_rows(post_processor.alpha))
    
    # Save num components
    components_file = os.path.join(out_dir, 'components.tsv')
    writer = csv.writer(open(components_file, 'w'), delimiter='\t')
    writer.writerows(list_to_csv_rows(post_processor.num_components))
    
    # Save cellular frequencies.
    cellular_freq_dir = os.path.join(out_dir, 'cellular_frequencies')
    
    if not os.path.exists(cellular_freq_dir):
        os.makedirs(cellular_freq_dir)
    
    cellular_freqs = post_processor.cellular_frequencies
    
    for gene in post_processor.genes:
        gene_file = os.path.join(cellular_freq_dir, "{0}.tsv".format(gene))
        
        fh = open(gene_file, 'w')
        
        writer = csv.writer(fh, delimiter='\t')
        
        writer.writerows(list_to_csv_rows(cellular_freqs[gene]))
        
        fh.close()
    
    # Save similarity matrix
    sim_mat_file = os.path.join(out_dir, "similarity_matrix.tsv")
    writer = csv.writer(open(sim_mat_file, 'w'), delimiter='\t')
    writer.writerows(post_processor.similarity_matrix)
    
def list_to_csv_rows(x):
    return [[x_i, ] for x_i in x]
