#include "TROOT.h"
#include "TFile.h"
#include "TCanvas.h"
#include "TH2D.h"
#include "TStyle.h"

void tmp() {
  gROOT->SetBatch(kTRUE);
  TFile *f = TFile::Open("/scratch-cbe/users/alikaan.gueven/AN_plots/checks_2023/2023v2018_v4_jet/data/post/met_2023_hist.root");
  f->cd("all_Jet_all");
  TH2D *h = (TH2D*)gDirectory->Get("Jet_eta_vs_Jet_phi");
  gStyle->SetPalette(kViridis);
  TCanvas *c = new TCanvas("c","",1200,800);
  h->Draw("COLZ");
  c->SaveAs("Jet_eta_vs_Jet_phi.png");
}
