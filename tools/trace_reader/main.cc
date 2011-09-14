#include <cassert>
#include <fstream>
#include <zlib.h>

#include "all_knobs.h"
#include "knob.h"
#include "trace_read.h"

int read_trace(string trace_path)
{
  string base_filename = trace_path.substr(0, trace_path.find_last_of("."));
  ifstream trace_file(trace_path.c_str());

  if (trace_file.fail()) {
    cout << "> error: trace file does not exist!\n";
    exit(0);
  }

  int num_thread;
  string type;
  int max_block_per_core;
  int inst_count = 0;

  // read number of threads and type of trace
  trace_file >> num_thread >> type;
  if (type == "newptx") {
    trace_file >> max_block_per_core;
  }

  // open each thread trace file
  for (int ii = 0; ii < num_thread; ++ii) {
    int tid;
    int start_inst_count;

    // set up thread trace file name
    trace_file >> tid >> start_inst_count;
    stringstream sstr;
    sstr << base_filename << "_" << tid << ".raw";

    string thread_filename;
    sstr >> thread_filename;

    // open thread trace file
    gzFile gztrace = gzopen(thread_filename.c_str(), "r");

    const int trace_buffer_size = 100000;
    char trace_buffer[trace_buffer_size * TRACE_SIZE];

    while (1) {
      int byte_read = gzread(gztrace, trace_buffer, trace_buffer_size * TRACE_SIZE);
      byte_read /= TRACE_SIZE;
      inst_count += byte_read;

      if (byte_read != trace_buffer_size) {
        break;
      }
    } 
    gzclose(gztrace);
  }
  cout << "> trace_path: " << trace_path << " inst_count: " << inst_count << "\n";

  return inst_count;
}


int main(int argc, char* argv[])
{
  KnobsContainer* knob_container = new KnobsContainer();
  all_knobs_c* knobs = knob_container->getAllKnobs();

  if (argc < 2) {
    cout << "> error: specify trace path\n";
    exit(0);
  }

  string trace_path(argv[1]);
  cout << "> trace_path: " << trace_path << "\n";

  string base_filename = trace_path.substr(0, trace_path.find_last_of("."));
  ifstream trace_file(trace_path.c_str());

  if (trace_file.fail()) {
    cout << "> error: trace file does not exist!\n";
    exit(0);
  }

  int num_thread;
  string type;
  int max_block_per_core;

  // read number of threads and type of trace
  trace_file >> num_thread >> type;

  int64_t inst_count = 0;
  if (type == "newptx") {
    while (trace_file >> trace_path) {
      inst_count += read_trace(trace_path);
    }
  }
  else {
    trace_file.close();
    inst_count += read_trace(trace_path);
  }


  cout << "> Total instruction count: " << inst_count << "\n";


  return 0;
}