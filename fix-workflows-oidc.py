#!/usr/bin/env python3
"""
Script to update GitHub Actions workflows to use OIDC authentication instead of access keys.
"""

import os
import re

def update_workflow_file(filepath):
    """Update a single workflow file to use OIDC authentication."""
    print(f"Updating {filepath}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Add permissions section after the 'on' section if not present
    if 'permissions:' not in content:
        # Find the position after the 'on:' section
        on_pattern = r'(on:\s*\n(?:(?:\s+\w+.*\n)*(?:\s+-.*\n)*)*)'
        match = re.search(on_pattern, content)
        if match:
            on_section = match.group(1)
            permissions_section = f"""{on_section}
# Required for OIDC authentication with AWS
permissions:
  id-token: write
  contents: read

"""
            content = content.replace(on_section, permissions_section)
    
    # Replace AWS credentials configuration
    old_creds_pattern = r'''aws-access-key-id: \$\{\{ secrets\.AWS_ACCESS_KEY_ID(?:_STAGING)? \}\}
\s+aws-secret-access-key: \$\{\{ secrets\.AWS_SECRET_ACCESS_KEY(?:_STAGING)? \}\}
\s+aws-region: \$\{\{ env\.AWS_REGION \}\}'''
    
    # Determine which role to use based on file name
    if 'staging' in filepath.lower():
        role_arn = '${{ secrets.AWS_ROLE_ARN_STAGING }}'
        session_name = 'GitHubActions-Staging'
    else:
        role_arn = '${{ secrets.AWS_ROLE_ARN_PRODUCTION }}'
        session_name = 'GitHubActions-Production'
    
    new_creds = f'''role-to-assume: {role_arn}
        role-session-name: {session_name}
        aws-region: ${{{{ env.AWS_REGION }}}}'''
    
    content = re.sub(old_creds_pattern, new_creds, content, flags=re.MULTILINE)
    
    # Also handle the case where secrets are referenced differently
    content = re.sub(
        r'aws-access-key-id: \$\{\{ secrets\.AWS_ACCESS_KEY_ID \}\}\s*\n\s*aws-secret-access-key: \$\{\{ secrets\.AWS_SECRET_ACCESS_KEY \}\}\s*\n\s*aws-region: \$\{\{ env\.AWS_REGION \}\}',
        f'role-to-assume: ${{{{ secrets.AWS_ROLE_ARN_PRODUCTION }}}}\n        role-session-name: GitHubActions-Production\n        aws-region: ${{{{ env.AWS_REGION }}}}',
        content,
        flags=re.MULTILINE
    )
    
    content = re.sub(
        r'aws-access-key-id: \$\{\{ secrets\.AWS_ACCESS_KEY_ID_STAGING \}\}\s*\n\s*aws-secret-access-key: \$\{\{ secrets\.AWS_SECRET_ACCESS_KEY_STAGING \}\}\s*\n\s*aws-region: \$\{\{ env\.AWS_REGION \}\}',
        f'role-to-assume: ${{{{ secrets.AWS_ROLE_ARN_STAGING }}}}\n        role-session-name: GitHubActions-Staging\n        aws-region: ${{{{ env.AWS_REGION }}}}',
        content,
        flags=re.MULTILINE
    )
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {filepath}")

def main():
    """Update all workflow files."""
    workflows_dir = '.github/workflows'
    
    if not os.path.exists(workflows_dir):
        print(f"❌ Directory {workflows_dir} not found")
        return
    
    workflow_files = [
        'staging.yml',
        'release.yml',
        'rollback.yml',
        'monitoring.yml'
    ]
    
    for filename in workflow_files:
        filepath = os.path.join(workflows_dir, filename)
        if os.path.exists(filepath):
            update_workflow_file(filepath)
        else:
            print(f"⚠️ File {filepath} not found, skipping")
    
    print("\n🎉 All workflow files updated!")
    print("\nNext steps:")
    print("1. Set up AWS OIDC provider (see AWS_OIDC_SETUP.md)")
    print("2. Create IAM roles for GitHub Actions")
    print("3. Update GitHub secrets:")
    print("   - Add: AWS_ROLE_ARN_PRODUCTION")
    print("   - Add: AWS_ROLE_ARN_STAGING")
    print("   - Remove: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
    print("   - Remove: AWS_ACCESS_KEY_ID_STAGING, AWS_SECRET_ACCESS_KEY_STAGING")

if __name__ == '__main__':
    main()