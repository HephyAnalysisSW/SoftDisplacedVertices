import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.Math.MinimizerOptions.SetDefaultMaxFunctionCalls(3000000)
ROOT.Math.MinimizerOptions.SetDefaultMaxIterations(300000)

input_path = "/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/AN-25-092_ML_plots3/bkg_run2/all_run2_hist.root"
rebin_factor = 4


def load_hist(root_file, name, clone_name):
    hist = root_file.Get(name)
    hist = hist.Clone(clone_name)
    hist.SetDirectory(0)
    hist.Rebin(rebin_factor)
    hist.Scale(1.0 / hist.Integral(1, hist.GetNbinsX()))
    return hist


def poly_expr(order):
    terms = []
    for i in range(order + 1):
        if i == 0:
            terms.append(f"[{i}]")
        elif i == 1:
            terms.append(f"[{i}]*x")
        else:
            terms.append(f"[{i}]*" + "*".join(["x"] * i))
    return " + ".join(terms)


def cheb_expr(order):
    terms = ["[0]"]
    for i in range(1, order + 1):
        terms.append(f"[{i}]*cos({i}*acos(2*x-1))")
    return " + ".join(terms)


def fit_candidate(name, expr, params, limits=()):
    func = ROOT.TF1(name, expr, first_x, last_x)
    func.SetNpx(5000)
    for i, value in enumerate(params):
        func.SetParameter(i, value)
    for idx, low, high in limits:
        func.SetParLimits(idx, low, high)

    status = ratio.Fit(func, "QMRNS0")
    chi2 = func.GetChisquare()
    ndf = func.GetNDF()
    prob = ROOT.TMath.Prob(chi2, ndf) if ndf > 0 else 0.0
    print(
        f"{name}: status={int(status)} chi2={chi2:.6f} ndf={ndf} "
        f"chi2/ndf={chi2 / ndf if ndf > 0 else 0.0:.6f} p={prob:.8g}"
    )
    print("  params =", [func.GetParameter(i) for i in range(func.GetNpar())])
    return prob, chi2, ndf, name, [func.GetParameter(i) for i in range(func.GetNpar())]


f_in = ROOT.TFile.Open(input_path)
h_k0 = load_hist(f_in, "all_evt/k0_Max_ML_score", "h_k0_scan")
h_nob0 = load_hist(f_in, "all_evt/nob0_Max_ML_score", "h_nob0_scan")
f_in.Close()

ratio = h_k0.Clone("ratio_k0_scan")
ratio.Divide(h_nob0)

first_x = ratio.GetBinCenter(1)
last_x = ratio.GetBinCenter(ratio.GetNbinsX())
best = None

for order in range(4, 21):
    expr = poly_expr(order)
    params = [1.0] + [0.0] * order
    result = fit_candidate(f"poly{order}", expr, params)
    best = result if best is None or result[0] > best[0] else best

for order in range(4, 31):
    expr = cheb_expr(order)
    params = [0.5] + [0.0] * order
    result = fit_candidate(f"cheb{order}", expr, params)
    best = result if result[0] > best[0] else best

for order in range(4, 17):
    amp = order + 1
    tau = order + 2
    expr = poly_expr(order) + f" + [{amp}]*exp(-(x-{first_x})/[{tau}])"
    params = [1.0] + [0.0] * order + [1.0, 0.001]
    limits = [(amp, 0.0, 10.0), (tau, 1.0e-6, 1.0)]
    result = fit_candidate(f"poly{order}_shifted_exp", expr, params, limits)
    best = result if result[0] > best[0] else best

print("BEST", best)
