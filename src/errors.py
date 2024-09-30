from config import BASE_DIR

has_new_errors = False

# Clear the existing error log
with open(BASE_DIR.parent / "error.log", 'w') as f:
  f.write('')

def write_to_error_log(contents):
  """Write contents to an error log file."""
  global has_new_errors
  error_log_path = BASE_DIR.parent / "error.log"
  has_new_errors = True
  if not error_log_path.exists():
    with open(error_log_path, 'w') as f:
      f.write('')
  with open(error_log_path, 'a') as f:
    if not contents.endswith('\n'):
      contents += '\n'
    f.write(contents)
  
def error_log_has_new_errors():
  """Returns true if the error log has new errors during this run."""
  global has_new_errors;
  return has_new_errors