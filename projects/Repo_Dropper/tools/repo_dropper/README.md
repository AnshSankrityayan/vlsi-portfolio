# Repo Dropper User Manual

Repo Dropper is a local desktop app for building a clean VLSI portfolio repo.
It copies files from your working folders into a GitHub-friendly structure and
can commit and push them.

## 1. Open the App

From this repository:

```bash
cd /home/fmitadmin/Downloads/fluid_controller-20260606T030042Z-3-001
./run_repo_dropper.sh
```

If you created the virtual environment for drag-and-drop support:

```bash
cd /home/fmitadmin/Downloads/fluid_controller-20260606T030042Z-3-001
source .venv/bin/activate
./run_repo_dropper.sh
```

## 2. Optional Drag-and-Drop Setup

Ubuntu blocks global `pip install`, so use a virtual environment:

```bash
cd /home/fmitadmin/Downloads/fluid_controller-20260606T030042Z-3-001
python3 -m venv .venv
source .venv/bin/activate
pip install -r tools/repo_dropper/requirements.txt
./run_repo_dropper.sh
```

If `venv` is missing:

```bash
sudo apt install python3-venv
```

The app still works without drag-and-drop. Click **Add files** or **Add folder**.

## 3. Best Daily Workflow

1. Type a project name.

Example:

```text
01_nand2
```

2. Keep **Placement** as:

```text
auto
```

3. Click **Add folder** and choose your project folder.

Example:

```text
/home/fmitadmin/vlsi_workspace/day1/
```

4. Check the table. It should auto-sort files into:

```text
rtl
tb
sim
waves
synthesis
docs
```

5. Click **Copy into repo**.

6. Type a commit message.

Example:

```text
Add NAND2 gate project
```

7. Click **Git add + commit**.

8. Click **Push**.

## 4. Example: Your NAND2 Folder

If your source folder contains:

```text
/home/fmitadmin/vlsi_workspace/day1/nand2.v
/home/fmitadmin/vlsi_workspace/day1/nand2_tb.v
/home/fmitadmin/vlsi_workspace/day1/nand2_sim
/home/fmitadmin/vlsi_workspace/day1/nand2_wave.vcd
/home/fmitadmin/vlsi_workspace/day1/synth.ys
/home/fmitadmin/vlsi_workspace/day1/nand2.json
/home/fmitadmin/vlsi_workspace/day1/nand2.svg
```

Repo Dropper will create:

```text
projects/01_nand2/rtl/nand2.v
projects/01_nand2/tb/nand2_tb.v
projects/01_nand2/sim/nand2_sim
projects/01_nand2/waves/nand2_wave.vcd
projects/01_nand2/synthesis/synth.ys
projects/01_nand2/synthesis/nand2.json
projects/01_nand2/synthesis/nand2.svg
projects/01_nand2/README.md
```

## 5. What Each Control Does

**Project**

The folder name under `projects/`. Use names like:

```text
01_nand2
02_comparator
03_thermostat
```

**Placement**

Use `auto` for normal work. The app guesses the right folder:

```text
*_tb.v      -> tb
*.v, *.sv   -> rtl
*.vcd       -> waves
*.ys        -> synthesis
*.json      -> synthesis
*.svg       -> synthesis
scripts     -> sim
```

You can also force every selected file into one folder by choosing `rtl`, `tb`,
`sim`, `waves`, `synthesis`, or `docs`.

**Add files**

Choose individual files.

**Add folder**

Choose a whole project folder. This is the easiest option.

**Auto-sort**

Re-runs the file sorting rules.

**Copy into repo**

Copies the files into `projects/<project_name>/...`.

**Git add + commit**

Stages the safe portfolio paths and commits them.

**Push**

Uploads the commit to GitHub. This works only after you configure a remote.

## 6. Connect to GitHub

Create an empty GitHub repo first, then run:

```bash
git remote add origin <your-github-repo-url>
git branch -M main
git push -u origin main
```

After that, the app's **Push** button should work.

## 7. Important Safety Notes

Do not push generated build folders like:

```text
.pio/
.venv/
__pycache__/
```

They are ignored by `.gitignore`. The app also avoids scanning those folders.

If Git already staged build files by mistake, unstage them with:

```bash
git rm --cached -r --ignore-unmatch fluid_controller/.pio .venv
```

That does not delete your files. It only removes them from the next commit.

## 8. Recommended Portfolio Structure

Each project should look like this:

```text
projects/01_project_name/
├── README.md
├── rtl/
├── tb/
├── sim/
├── waves/
├── synthesis/
└── docs/
```

This makes your repo easy for recruiters and interviewers to scan.
